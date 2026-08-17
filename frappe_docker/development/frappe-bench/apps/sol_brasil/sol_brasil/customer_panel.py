from datetime import date

import frappe
from frappe import _
from frappe.utils import cint, flt, getdate


@frappe.whitelist()
def get_customer_panel(customer: str, year=None):
	frappe.has_permission("Customer", "read", customer, throw=True)
	year = cint(year) or date.today().year

	return {
		"year": year,
		"available_years": _available_years(customer),
		"contracts": _contracts(customer),
		"open_invoices": _open_invoices(customer),
		"paid_invoices": _paid_invoices(customer, year),
		"issues": _issues(customer),
		"service_orders": _service_orders(customer),
	}


@frappe.whitelist()
def get_available_contracts(customer: str):
	frappe.has_permission("Customer", "read", customer, throw=True)
	return [
		row
		for row in _contracts(customer)
		if row.status not in ("Cancelled", "Completed")
	]


def _contracts(customer):
	rows = frappe.get_all(
		"Subscription",
		filters={"party_type": "Customer", "party": customer},
		fields=["name", "status", "start_date", "end_date"],
		order_by="start_date desc",
	)

	for row in rows:
		plans = frappe.get_all(
			"Subscription Plan Detail",
			filters={"parent": row.name, "parenttype": "Subscription"},
			fields=["plan", "qty"],
			order_by="idx asc",
		)
		row.plans = ", ".join(plan.plan for plan in plans) or _("Sem plano")
		row.monthly_value = sum(
			flt(frappe.db.get_value("Subscription Plan", plan.plan, "cost")) * (plan.qty or 1)
			for plan in plans
		)
	return rows


def _open_invoices(customer):
	return frappe.get_all(
		"Sales Invoice",
		filters={"customer": customer, "docstatus": 1, "outstanding_amount": [">", 0]},
		fields=[
			"name",
			"posting_date",
			"due_date",
			"grand_total",
			"outstanding_amount",
			"currency",
			"status",
		],
		order_by="due_date asc",
	)


def _paid_invoices(customer, year):
	return frappe.get_all(
		"Sales Invoice",
		filters={
			"customer": customer,
			"docstatus": 1,
			"status": "Paid",
			"posting_date": ["between", [f"{year}-01-01", f"{year}-12-31"]],
		},
		fields=[
			"name",
			"posting_date",
			"due_date",
			"grand_total",
			"outstanding_amount",
			"currency",
			"status",
		],
		order_by="posting_date desc",
	)


def _available_years(customer):
	dates = frappe.get_all(
		"Sales Invoice",
		filters={"customer": customer, "docstatus": 1},
		pluck="posting_date",
	)
	years = {getdate(value).year for value in dates if value}
	years.add(date.today().year)
	return sorted(years, reverse=True)


def _issues(customer):
	return frappe.get_all(
		"Issue",
		filters={"customer": customer},
		fields=["name", "subject", "status", "priority", "opening_date"],
		order_by="opening_date desc, creation desc",
		limit_page_length=50,
	)


def _service_orders(customer):
	return frappe.get_all(
		"Maintenance Visit",
		filters={"customer": customer, "docstatus": ["<", 2]},
		fields=[
			"name",
			"mntc_date",
			"mntc_time",
			"maintenance_type",
			"completion_status",
			"status",
			"docstatus",
		],
		order_by="mntc_date desc, creation desc",
		limit_page_length=50,
	)
