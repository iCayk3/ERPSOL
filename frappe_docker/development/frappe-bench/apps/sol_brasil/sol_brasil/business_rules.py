import frappe
from frappe import _
from frappe.utils import cint, date_diff, getdate, today


AUTOMATIC_STATUSES = ("Aguardando instalação", "Ativo", "Bloqueado", "Suspenso")
CUSTOMER_STATUS_PRIORITY = ("Ativo", "Aguardando instalação", "Bloqueado", "Suspenso", "Cancelado")


def _settings():
	settings = frappe.get_single("Regras de Negocio")
	return {
		"enabled": bool(cint(settings.enabled)),
		"block_days": cint(settings.block_after_days or 5),
		"suspend_days": cint(settings.suspend_after_days or 15),
	}


def _maximum_overdue_days(subscription):
	due_dates = frappe.get_all(
		"Sales Invoice",
		filters={
			"subscription": subscription,
			"docstatus": 1,
			"outstanding_amount": [">", 0],
			"due_date": ["<", today()],
		},
		pluck="due_date",
	)
	return max((date_diff(getdate(today()), getdate(due_date)) for due_date in due_dates), default=0)


def recalculate_customer_status(customer):
	if not customer or not frappe.db.exists("Customer", customer):
		return
	statuses = set(frappe.get_all(
		"Subscription",
		filters={"party_type": "Customer", "party": customer},
		pluck="custom_connection_status",
	))
	status = next((value for value in CUSTOMER_STATUS_PRIORITY if value in statuses), "Aguardando instalação")
	frappe.db.set_value("Customer", customer, "custom_connection_status", status, update_modified=False)


def _plan_policy(subscription):
	plan = frappe.db.get_value("Subscription", subscription, "custom_internet_plan")
	plan = plan or frappe.db.get_value(
		"Subscription Plan Detail", {"parent": subscription, "parenttype": "Subscription"}, "plan"
	)
	if not plan:
		return {"plan": None, "download": 0, "upload": 0, "reduce_bandwidth": False}
	values = frappe.db.get_value(
		"Subscription Plan",
		plan,
		[
			"custom_download_mbps", "custom_upload_mbps", "custom_enable_overdue_reduction",
			"custom_reduce_after_days", "custom_download_reduction_percent",
			"custom_upload_reduction_percent",
		],
		as_dict=True,
	)
	return {
		"plan": plan,
		"download": cint(values.custom_download_mbps),
		"upload": cint(values.custom_upload_mbps),
		"reduce_bandwidth": bool(cint(values.custom_enable_overdue_reduction)),
		"reduce_days": cint(values.custom_reduce_after_days or 1),
		"download_reduction": float(values.custom_download_reduction_percent or 0),
		"upload_reduction": float(values.custom_upload_reduction_percent or 0),
	}


def _effective_bandwidth(subscription, status, reduced, policy=None):
	policy = policy or _plan_policy(subscription)
	download, upload = policy["download"], policy["upload"]
	if status in ("Bloqueado", "Suspenso", "Cancelado"):
		download = upload = 0
	elif reduced:
		download = max(1, round(download * (100 - policy["download_reduction"]) / 100)) if download else 0
		upload = max(1, round(upload * (100 - policy["upload_reduction"]) / 100)) if upload else 0
	return {
		"custom_bandwidth_reduced": 1 if reduced else 0,
		"custom_effective_download_mbps": download,
		"custom_effective_upload_mbps": upload,
		"custom_effective_rate_limit": f"{upload}M/{download}M" if upload or download else "0M/0M",
	}


def recalculate_contract_status(subscription, allow_cancelled=False):
	if hasattr(subscription, "name"):
		subscription = subscription.name
	row = frappe.db.get_value(
		"Subscription",
		subscription,
		["party_type", "party", "custom_pppoe_username", "custom_connection_status"],
		as_dict=True,
	)
	if not row or row.party_type != "Customer":
		return None
	if row.custom_connection_status == "Cancelado" and not allow_cancelled:
		previous_rate = frappe.db.get_value("Subscription", subscription, "custom_effective_rate_limit")
		frappe.db.set_value(
			"Subscription",
			subscription,
			_effective_bandwidth(subscription, "Cancelado", False),
			update_modified=False,
		)
		recalculate_customer_status(row.party)
		if previous_rate != "0M/0M":
			from sol_brasil.radius_provisioning import queue_subscription
			queue_subscription(subscription)
		return "Cancelado"

	settings = _settings()
	policy = _plan_policy(subscription)
	overdue_days = _maximum_overdue_days(subscription) if settings["enabled"] else 0
	reduced = False
	if not row.custom_pppoe_username:
		new_status = "Aguardando instalação"
	elif not settings["enabled"]:
		new_status = "Ativo"
	else:
		if overdue_days >= settings["suspend_days"]:
			new_status = "Suspenso"
		elif overdue_days >= settings["block_days"]:
			new_status = "Bloqueado"
		else:
			new_status = "Ativo"
			reduced = policy["reduce_bandwidth"] and overdue_days >= policy["reduce_days"]

	values = {"custom_connection_status": new_status}
	values.update(_effective_bandwidth(subscription, new_status, reduced, policy))
	previous = frappe.db.get_value(
		"Subscription", subscription,
		["custom_connection_status", "custom_bandwidth_reduced", "custom_effective_rate_limit"],
		as_dict=True,
	)
	frappe.db.set_value("Subscription", subscription, values, update_modified=False)
	recalculate_customer_status(row.party)
	if previous and any(str(previous.get(key) or "") != str(values.get(key) or "") for key in values):
		from sol_brasil.radius_provisioning import queue_subscription
		queue_subscription(subscription)
	return new_status


def recalculate_all_contract_statuses():
	for index, subscription in enumerate(frappe.get_all("Subscription", pluck="name"), start=1):
		recalculate_contract_status(subscription)
		if index % 100 == 0:
			frappe.db.commit()
	frappe.db.commit()


def refresh_from_invoice(doc, method=None):
	if doc.get("subscription"):
		recalculate_contract_status(doc.subscription)


def refresh_from_payment(doc, method=None):
	subscriptions = set()
	for reference in doc.get("references") or []:
		if reference.reference_doctype != "Sales Invoice":
			continue
		subscription = frappe.db.get_value("Sales Invoice", reference.reference_name, "subscription")
		if subscription:
			subscriptions.add(subscription)
	for subscription in subscriptions:
		recalculate_contract_status(subscription)


def refresh_from_plan(doc, method=None):
	subscriptions = set(frappe.get_all(
		"Subscription Plan Detail",
		filters={"plan": doc.name, "parenttype": "Subscription"},
		pluck="parent",
	))
	subscriptions.update(frappe.get_all(
		"Subscription", filters={"custom_internet_plan": doc.name}, pluck="name"
	))
	for subscription in subscriptions:
		recalculate_contract_status(subscription)


@frappe.whitelist()
def cancel_contract(subscription):
	frappe.has_permission("Subscription", "write", subscription, throw=True)
	contract = frappe.db.get_value("Subscription", subscription, ["party_type", "party"], as_dict=True)
	if not contract or contract.party_type != "Customer":
		frappe.throw(_("Selecione um contrato de cliente válido."))
	frappe.db.set_value("Subscription", subscription, "custom_connection_status", "Cancelado")
	recalculate_customer_status(contract.party)
	from sol_brasil.radius_provisioning import queue_subscription
	queue_subscription(subscription)
	return "Cancelado"


@frappe.whitelist()
def reactivate_contract(subscription):
	frappe.has_permission("Subscription", "write", subscription, throw=True)
	return recalculate_contract_status(subscription, allow_cancelled=True)
