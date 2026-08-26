import json
import re
from ipaddress import ip_address

import frappe
from frappe import _
from frappe.desk.search import validate_and_sanitize_search_inputs
from frappe.utils import add_days, cint
from frappe.utils import get_link_to_form


CONTRACT_ACTIVITY_FIELDS = {
	"status": "Situação",
	"custom_installation_address": "Endereço de instalação",
	"start_date": "Início do contrato",
	"end_date": "Término do contrato",
	"current_invoice_start": "Início da fatura atual",
	"current_invoice_end": "Término da fatura atual",
	"days_until_due": "Dias até o vencimento",
	"generate_invoice_at": "Gerar fatura em",
	"cancel_at_period_end": "Cancelar ao final do período",
	"plans": "Planos",
}


def _contract_customer(doc):
	return doc.party if doc.party_type == "Customer" and doc.party else None


def _activity_value(value):
	if value in (None, ""):
		return "vazio"
	if isinstance(value, bool):
		return "Sim" if value else "Não"
	if isinstance(value, list):
		plans = [row.get("plan") for row in value if row.get("plan")]
		return ", ".join(plans) or "nenhum"
	return str(value)


def _add_customer_contract_activity(customer, text):
	if not customer or not frappe.db.exists("Customer", customer):
		return
	frappe.get_doc("Customer", customer).add_comment("Comment", text=text)


def register_contract_creation(doc, method=None):
	customer = _contract_customer(doc)
	if not customer:
		return
	link = get_link_to_form("Subscription", doc.name, doc.name)
	_add_customer_contract_activity(customer, _("Contrato {0} criado para este cliente.").format(link))


def register_contract_update(doc, method=None):
	previous = doc.get_doc_before_save()
	if not previous:
		return
	customer = _contract_customer(doc) or _contract_customer(previous)
	if not customer:
		return

	changes = []
	for fieldname, label in CONTRACT_ACTIVITY_FIELDS.items():
		old_value = previous.get(fieldname)
		new_value = doc.get(fieldname)
		if fieldname == "plans":
			old_value = [row.as_dict() for row in (old_value or [])]
			new_value = [row.as_dict() for row in (new_value or [])]
		if old_value == new_value:
			continue
		changes.append(
			_('{0}: de "{1}" para "{2}"').format(
				label, _activity_value(old_value), _activity_value(new_value)
			)
		)

	if changes:
		link = get_link_to_form("Subscription", doc.name, doc.name)
		_add_customer_contract_activity(
			customer,
			_("Contrato {0} alterado: {1}.").format(link, "; ".join(changes)),
		)


def register_contract_deletion(doc, method=None):
	customer = _contract_customer(doc)
	if customer:
		_add_customer_contract_activity(
			customer,
			_("Contrato {0} excluído da ficha do cliente.").format(frappe.bold(doc.name)),
		)


def _customer_address_names(customer):
	if not customer:
		return []
	return frappe.get_all(
		"Dynamic Link",
		filters={
			"parenttype": "Address",
			"link_doctype": "Customer",
			"link_name": customer,
		},
		pluck="parent",
	)


@frappe.whitelist()
def get_customer_addresses(customer):
	frappe.has_permission("Customer", "read", customer, throw=True)
	names = _customer_address_names(customer)
	if not names:
		return []
	rows = frappe.get_all(
		"Address",
		filters={"name": ["in", names], "disabled": 0},
		fields=[
			"name", "address_title", "address_type", "address_line1", "address_line2",
			"city", "state", "pincode", "is_primary_address",
		],
		order_by="is_primary_address desc, modified desc",
	)
	for row in rows:
		row.label = " — ".join(filter(None, [row.address_title or row.name, row.address_line1, row.city]))
	return rows


@frappe.whitelist()
@validate_and_sanitize_search_inputs
def address_query(doctype, txt, searchfield, start, page_len, filters):
	customer = (filters or {}).get("customer")
	names = _customer_address_names(customer)
	if not names:
		return []
	return frappe.db.sql(
		"""
		SELECT name, CONCAT_WS(' — ', address_title, address_line1, city)
		FROM `tabAddress`
		WHERE disabled = 0 AND name IN %(names)s
			AND (name LIKE %(txt)s OR address_title LIKE %(txt)s
				OR address_line1 LIKE %(txt)s OR city LIKE %(txt)s)
		ORDER BY is_primary_address DESC, modified DESC
		LIMIT %(start)s, %(page_len)s
		""",
		{"names": names, "txt": f"%{txt}%", "start": start, "page_len": page_len},
	)


def validate_installation_address(doc, method=None):
	if doc.party_type != "Customer":
		return
	plans = [row.plan for row in (doc.get("plans") or []) if row.plan]
	doc.custom_internet_plan = plans[0] if plans else None
	if not doc.custom_installation_address:
		_validate_pppoe_and_network(doc)
		requires_address = bool(doc.get("custom_pppoe_username")) or doc.get("custom_connection_status") in (
			"Ativo", "Suspenso", "Bloqueado",
		)
		if requires_address and not doc.flags.get("in_access_migration"):
			frappe.throw(
				_("Selecione o endereço de instalação deste contrato."),
				title=_("Endereço obrigatório"),
			)
		return
	if doc.custom_installation_address not in _customer_address_names(doc.party):
		frappe.throw(
			_("O endereço de instalação selecionado não pertence a este cliente."),
			title=_("Endereço inválido"),
		)
	_validate_pppoe_and_network(doc)


def _validate_pppoe_and_network(doc):
	username = (doc.get("custom_pppoe_username") or "").strip().lower()
	doc.custom_pppoe_username = username
	if username and any(character.isspace() for character in username):
		frappe.throw(_("O usuário PPPoE não pode conter espaços."))
	if username and not doc.get("custom_pppoe_password"):
		frappe.throw(_("Informe a senha PPPoE deste contrato."))
	if doc.get("custom_pppoe_password") and not username:
		frappe.throw(_("Informe o usuário PPPoE deste contrato."))

	if doc.get("custom_ipv4_address"):
		try:
			address = ip_address(doc.custom_ipv4_address.strip())
		except ValueError:
			frappe.throw(_("Informe um endereço IPv4 válido."))
		if address.version != 4:
			frappe.throw(_("O campo Endereço IPv4 aceita somente IPv4."))
		doc.custom_ipv4_address = str(address)

	if doc.get("custom_mac_address"):
		hexadecimal = re.sub(r"[^0-9A-Fa-f]", "", doc.custom_mac_address)
		if len(hexadecimal) != 12:
			frappe.throw(_("Informe um endereço MAC válido."))
		doc.custom_mac_address = ":".join(
			hexadecimal[index : index + 2].upper() for index in range(0, 12, 2)
		)

	vlan = cint(doc.get("custom_vlan_id"))
	if vlan and not 1 <= vlan <= 4094:
		frappe.throw(_("A VLAN deve estar entre 1 e 4094."))
	onu_number = cint(doc.get("custom_onu_number"))
	if onu_number and not 1 <= onu_number <= 512:
		frappe.throw(_("O número da ONU deve estar entre 1 e 512."))


@frappe.whitelist()
def map_contract_to_sales_invoice(source_name, target_doc=None):
	"""Preenche uma fatura avulsa com cliente, período e planos do contrato."""
	contract = frappe.get_doc("Subscription", source_name)
	contract.check_permission("read")
	if contract.party_type != "Customer":
		frappe.throw(_("Selecione um contrato de cliente."), title=_("Contrato inválido"))
	if contract.status in ("Cancelled", "Completed"):
		frappe.throw(_("Não é possível faturar um contrato cancelado ou encerrado."))

	if isinstance(target_doc, str):
		invoice = frappe.get_doc(json.loads(target_doc))
	elif target_doc:
		invoice = frappe.get_doc(target_doc)
	else:
		invoice = frappe.new_doc("Sales Invoice")

	if invoice.get("subscription") and invoice.subscription != contract.name:
		frappe.throw(_("A fatura já está vinculada a outro contrato."))
	if invoice.get("customer") and invoice.customer != contract.party:
		frappe.throw(_("O contrato selecionado pertence a outro cliente."))

	invoice.customer = contract.party
	invoice.company = contract.company or invoice.company
	invoice.subscription = contract.name
	invoice.from_date = contract.current_invoice_start
	invoice.to_date = contract.current_invoice_end
	invoice.currency = frappe.db.get_value("Subscription Plan", contract.plans[0].plan, "currency")
	invoice.cost_center = contract.cost_center or invoice.cost_center
	if contract.sales_tax_template:
		invoice.taxes_and_charges = contract.sales_tax_template
	invoice.apply_discount_on = contract.apply_additional_discount or invoice.apply_discount_on
	invoice.additional_discount_percentage = contract.additional_discount_percentage
	invoice.discount_amount = contract.additional_discount_amount

	posting_date = invoice.posting_date or frappe.utils.today()
	if contract.days_until_due:
		invoice.due_date = add_days(posting_date, cint(contract.days_until_due))

	for item in contract.get_items_from_plans(contract.plans, 0):
		invoice.append("items", item)

	invoice.run_method("set_missing_values")
	return invoice


def validate_invoice_contract(doc, method=None):
	if not doc.subscription:
		return
	contract = frappe.db.get_value(
		"Subscription", doc.subscription, ["party_type", "party", "status"], as_dict=True
	)
	if not contract or contract.party_type != "Customer" or contract.party != doc.customer:
		frappe.throw(
			_("O contrato vinculado não pertence ao cliente desta fatura."),
			title=_("Contrato inválido"),
		)
