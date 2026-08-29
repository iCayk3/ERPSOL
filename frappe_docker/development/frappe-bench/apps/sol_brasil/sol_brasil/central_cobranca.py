import frappe
from frappe import _
from frappe.utils import cint, flt, getdate, nowdate, today


def _reference_month_from_date(value):
	if not value:
		return None
	date = getdate(value)
	return f"{date.year:04d}-{date.month:02d}"


def _invoice_reference_month(doc):
	return (
		doc.get("custom_billing_reference_month")
		or _reference_month_from_date(doc.get("from_date"))
		or _reference_month_from_date(doc.get("posting_date"))
		or _reference_month_from_date(doc.get("due_date"))
	)


def set_invoice_reference_fields(doc, method=None):
	if not doc.get("custom_billing_reference_month"):
		doc.custom_billing_reference_month = _invoice_reference_month(doc)
	if doc.get("due_date") and not doc.get("custom_original_due_date"):
		doc.custom_original_due_date = doc.due_date


def _date_filter(period):
	if period == "overdue":
		return "si.due_date < %(today)s"
	if period == "today":
		return "si.due_date = %(today)s"
	if period == "upcoming":
		return "si.due_date > %(today)s"
	return "1 = 1"


def _status_filter(status):
	if status in ("Ativo", "Bloqueado", "Suspenso", "Aguardando instalação", "Cancelado"):
		return "COALESCE(sub.custom_connection_status, '') = %(connection_status)s"
	return "1 = 1"


def _reference_condition(reference_month):
	if reference_month:
		return "si.custom_billing_reference_month = %(reference_month)s"
	return "1 = 1"


def _summary(company=None, reference_month=None):
	conditions = ["si.docstatus = 1", "si.outstanding_amount > 0"]
	values = {"today": today(), "reference_month": reference_month}
	conditions.append(_reference_condition(reference_month))
	if company:
		conditions.append("si.company = %(company)s")
		values["company"] = company
	where = " AND ".join(conditions)
	rows = frappe.db.sql(
		f"""
		SELECT
			COUNT(*) AS open_count,
			COALESCE(SUM(si.outstanding_amount), 0) AS open_amount,
			COALESCE(SUM(COALESCE(NULLIF(si.custom_negotiated_amount, 0), si.outstanding_amount)), 0) AS collection_amount,
			SUM(CASE WHEN si.custom_renegotiated = 1 THEN 1 ELSE 0 END) AS renegotiated_count,
			SUM(CASE WHEN si.due_date < %(today)s THEN 1 ELSE 0 END) AS overdue_count,
			COALESCE(SUM(CASE WHEN si.due_date < %(today)s THEN si.outstanding_amount ELSE 0 END), 0) AS overdue_amount,
			SUM(CASE WHEN si.due_date = %(today)s THEN 1 ELSE 0 END) AS due_today_count,
			COALESCE(SUM(CASE WHEN si.due_date = %(today)s THEN si.outstanding_amount ELSE 0 END), 0) AS due_today_amount
		FROM `tabSales Invoice` si
		WHERE {where}
		""",
		values,
		as_dict=True,
	)
	status_rows = frappe.db.sql(
		f"""
		SELECT COALESCE(sub.custom_connection_status, 'Sem contrato') AS status, COUNT(*) AS total
		FROM `tabSales Invoice` si
		LEFT JOIN `tabSubscription` sub ON sub.name = si.subscription
		WHERE {where}
		GROUP BY COALESCE(sub.custom_connection_status, 'Sem contrato')
		ORDER BY total DESC
		""",
		values,
		as_dict=True,
	)
	data = rows[0] if rows else {}
	return {
		"open_count": cint(data.get("open_count")),
		"open_amount": flt(data.get("open_amount")),
		"collection_amount": flt(data.get("collection_amount")),
		"renegotiated_count": cint(data.get("renegotiated_count")),
		"overdue_count": cint(data.get("overdue_count")),
		"overdue_amount": flt(data.get("overdue_amount")),
		"due_today_count": cint(data.get("due_today_count")),
		"due_today_amount": flt(data.get("due_today_amount")),
		"by_status": status_rows,
	}


@frappe.whitelist()
def get_reference_months(company=None):
	frappe.has_permission("Sales Invoice", "read", throw=True)
	conditions = ["docstatus = 1", "custom_billing_reference_month IS NOT NULL", "custom_billing_reference_month != ''"]
	values = {}
	if company:
		conditions.append("company = %(company)s")
		values["company"] = company
	rows = frappe.db.sql(
		f"""
		SELECT custom_billing_reference_month AS value, COUNT(*) AS total
		FROM `tabSales Invoice`
		WHERE {" AND ".join(conditions)}
		GROUP BY custom_billing_reference_month
		ORDER BY custom_billing_reference_month DESC
		""",
		values,
		as_dict=True,
	)
	current = _reference_month_from_date(nowdate())
	default_month = current if any(row.value == current for row in rows) else (rows[0].value if rows else current)
	return {"months": rows, "default_month": default_month}


@frappe.whitelist()
def get_collection_center(period="overdue", reference_month=None, connection_status=None, company=None, limit=100):
	frappe.has_permission("Sales Invoice", "read", throw=True)
	limit = max(20, min(cint(limit or 100), 500))
	if not reference_month:
		reference_month = get_reference_months(company).get("default_month")
	values = {
		"today": today(),
		"period": period,
		"reference_month": reference_month,
		"connection_status": connection_status,
		"company": company,
		"limit": limit,
	}
	conditions = [
		"si.docstatus = 1",
		"si.outstanding_amount > 0",
		_date_filter(period),
		_reference_condition(reference_month),
		_status_filter(connection_status),
	]
	if company:
		conditions.append("si.company = %(company)s")
	where = " AND ".join(conditions)

	rows = frappe.db.sql(
		f"""
		SELECT
			si.name,
			si.customer,
			si.customer_name,
			si.company,
			si.posting_date,
			si.due_date,
			si.from_date,
			si.to_date,
			si.custom_billing_reference_month,
			si.custom_original_due_date,
			si.custom_renegotiated,
			si.custom_waive_interest_penalty,
			si.custom_negotiated_amount,
			si.status,
			si.currency,
			si.grand_total,
			si.outstanding_amount,
			COALESCE(NULLIF(si.custom_negotiated_amount, 0), si.outstanding_amount) AS collection_amount,
			si.subscription,
			GREATEST(DATEDIFF(%(today)s, si.due_date), 0) AS overdue_days,
			c.mobile_no,
			sub.custom_pppoe_username,
			sub.custom_connection_status,
			sub.custom_internet_plan
		FROM `tabSales Invoice` si
		LEFT JOIN `tabCustomer` c ON c.name = si.customer
		LEFT JOIN `tabSubscription` sub ON sub.name = si.subscription
		WHERE {where}
		ORDER BY
			CASE WHEN si.due_date < %(today)s THEN 0 ELSE 1 END,
			si.due_date ASC,
			si.outstanding_amount DESC
		LIMIT %(limit)s
		""",
		values,
		as_dict=True,
	)
	return {
		"summary": _summary(company, reference_month),
		"available_months": get_reference_months(company),
		"rows": rows,
		"filters": {
			"period": period,
			"reference_month": reference_month,
			"connection_status": connection_status,
			"company": company,
			"limit": limit,
		},
	}


@frappe.whitelist()
def recalculate_contracts():
	frappe.has_permission("Subscription", "write", throw=True)
	from sol_brasil.business_rules import recalculate_all_contract_statuses

	recalculate_all_contract_statuses()
	return _("Contratos recalculados.")


@frappe.whitelist()
def renegotiate_invoice(invoice, new_due_date, negotiated_amount=None, waive_interest_penalty=0, notes=None):
	frappe.has_permission("Sales Invoice", "write", invoice, throw=True)
	doc = frappe.get_doc("Sales Invoice", invoice)
	if doc.docstatus != 1:
		frappe.throw(_("Renegocie apenas faturas emitidas."))
	if flt(doc.outstanding_amount) <= 0:
		frappe.throw(_("A fatura selecionada não possui saldo em aberto."))
	if negotiated_amount in (None, ""):
		negotiated_amount = doc.get("custom_negotiated_amount") or doc.outstanding_amount
	negotiated_amount = flt(negotiated_amount)
	if negotiated_amount <= 0:
		frappe.throw(_("Informe um valor negociado maior que zero."))
	if not doc.get("custom_billing_reference_month"):
		frappe.db.set_value("Sales Invoice", invoice, "custom_billing_reference_month", _invoice_reference_month(doc))
	if not doc.get("custom_original_due_date"):
		frappe.db.set_value("Sales Invoice", invoice, "custom_original_due_date", doc.due_date)
	frappe.db.set_value(
		"Sales Invoice",
		invoice,
		{
			"due_date": new_due_date,
			"custom_renegotiated": 1,
			"custom_waive_interest_penalty": cint(waive_interest_penalty),
			"custom_negotiated_amount": negotiated_amount,
			"custom_renegotiation_notes": notes or "",
		},
		update_modified=True,
	)
	from sol_brasil.business_rules import refresh_from_invoice

	doc.reload()
	refresh_from_invoice(doc)
	return {
		"invoice": invoice,
		"due_date": new_due_date,
		"reference_month": doc.custom_billing_reference_month,
		"negotiated_amount": negotiated_amount,
		"waive_interest_penalty": cint(waive_interest_penalty),
	}


@frappe.whitelist()
def get_billing_report(reference_month=None, company=None):
	frappe.has_permission("Sales Invoice", "read", throw=True)
	if not reference_month:
		reference_month = get_reference_months(company).get("default_month")
	values = {"reference_month": reference_month, "company": company}
	conditions = ["si.docstatus = 1", "si.custom_billing_reference_month = %(reference_month)s"]
	if company:
		conditions.append("si.company = %(company)s")
	where = " AND ".join(conditions)
	summary = frappe.db.sql(
		f"""
		SELECT
			COUNT(*) AS invoices,
			COALESCE(SUM(si.grand_total), 0) AS billed,
			COALESCE(SUM(si.outstanding_amount), 0) AS open_amount,
			COALESCE(SUM(CASE
				WHEN si.outstanding_amount > 0
				THEN COALESCE(NULLIF(si.custom_negotiated_amount, 0), si.outstanding_amount)
				ELSE 0
			END), 0) AS collection_amount,
			SUM(CASE WHEN si.custom_renegotiated = 1 THEN 1 ELSE 0 END) AS renegotiated_count,
			COALESCE(SUM(si.grand_total - si.outstanding_amount), 0) AS received_by_invoice_balance
		FROM `tabSales Invoice` si
		WHERE {where}
		""",
		values,
		as_dict=True,
	)[0]
	received = frappe.db.sql(
		f"""
		SELECT COALESCE(SUM(per.allocated_amount), 0) AS received
		FROM `tabPayment Entry Reference` per
		INNER JOIN `tabPayment Entry` pe ON pe.name = per.parent
		INNER JOIN `tabSales Invoice` si ON si.name = per.reference_name
		WHERE per.reference_doctype = 'Sales Invoice'
			AND pe.docstatus = 1
			AND {where}
		""",
		values,
		as_dict=True,
	)[0]
	summary["received"] = flt(received.received)
	summary["reference_month"] = reference_month
	return summary


@frappe.whitelist()
def backfill_invoice_reference_months(ignore_permissions=False):
	if not ignore_permissions:
		frappe.has_permission("Sales Invoice", "write", throw=True)
	names = frappe.get_all("Sales Invoice", pluck="name")
	for index, name in enumerate(names, start=1):
		doc = frappe.get_doc("Sales Invoice", name)
		updates = {}
		if not doc.get("custom_billing_reference_month"):
			updates["custom_billing_reference_month"] = _invoice_reference_month(doc)
		if doc.get("due_date") and not doc.get("custom_original_due_date"):
			updates["custom_original_due_date"] = doc.due_date
		if updates:
			frappe.db.set_value("Sales Invoice", name, updates, update_modified=False)
		if index % 100 == 0:
			frappe.db.commit()
	frappe.db.commit()
	return len(names)
