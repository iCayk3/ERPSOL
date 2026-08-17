import frappe
from frappe.utils import getdate


DEMO_CUSTOMER = "Cliente Demonstração Fibra"
DEMO_ITEM = "PLANO-FIBRA-500-DEMO"
DEMO_PLAN = "Fibra 500 Mbps - Demonstração"


def create_demo_data():
	company = frappe.db.get_value("Company", {"name": ["like", "%Demo%"]}, "name")
	company = company or frappe.db.get_single_value("Global Defaults", "default_company")
	company = company or frappe.db.get_value("Company", {}, "name")
	if not company:
		frappe.throw("Cadastre uma empresa antes de criar os dados de demonstração.")

	company_doc = frappe.get_cached_doc("Company", company)
	_create_customer()
	_create_item()
	_create_plan(company_doc)
	_create_subscription(company_doc)

	invoices = []
	for reference, posting_date, due_date, paid in (
		("DEMO-ABERTO-01", "2026-07-01", "2026-07-10", False),
		("DEMO-ABERTO-02", "2026-08-01", "2026-09-10", False),
		("DEMO-PAGO-01", "2026-02-01", "2026-02-10", True),
		("DEMO-PAGO-02", "2026-05-01", "2026-05-10", True),
	):
		invoice = _create_invoice(company_doc, reference, posting_date, due_date)
		if paid and invoice.outstanding_amount:
			_create_payment(invoice)
		invoices.append(invoice.name)

	issue = _create_issue(company_doc)
	service_order = _create_service_order(company_doc)

	frappe.db.commit()
	return {
		"customer": DEMO_CUSTOMER,
		"plan": DEMO_PLAN,
		"invoices": invoices,
		"issue": issue,
		"service_order": service_order,
	}


def _create_customer():
	if frappe.db.exists("Customer", DEMO_CUSTOMER):
		frappe.db.set_value(
			"Customer",
			DEMO_CUSTOMER,
			{"custom_identity_document": "12.345.678-9", "custom_birth_date": "1990-04-15"},
		)
		return frappe.get_doc("Customer", DEMO_CUSTOMER)

	group = frappe.db.get_value("Customer Group", {"is_group": 0}, "name")
	territory = frappe.db.get_value("Territory", {"is_group": 0}, "name")
	doc = frappe.get_doc(
		{
			"doctype": "Customer",
			"customer_name": DEMO_CUSTOMER,
			"customer_type": "Individual",
			"customer_group": group,
			"territory": territory,
			"tax_id": "529.982.247-25",
			"custom_tax_document": "529.982.247-25",
			"custom_person_type": "Pessoa Física",
			"custom_identity_document": "12.345.678-9",
			"custom_birth_date": "1990-04-15",
			"custom_connection_status": "Ativo",
			"custom_subscription_plan": DEMO_PLAN,
			"custom_activation_date": "2026-01-15",
			"custom_pppoe_username": "demo.fibra500",
			"custom_pppoe_password": "demo@500",
			"custom_ipv4_address": "100.64.10.25",
			"custom_mac_address": "02:00:00:10:50:01",
			"custom_olt": "OLT-DEMO-01",
			"custom_pon": "1/1/4",
			"custom_onu_serial": "ONU-DEMO-500001",
		}
	)
	# O plano é criado logo depois; ignorar o link apenas durante a criação inicial.
	doc.flags.ignore_links = True
	doc.insert(ignore_permissions=True)
	return doc


def _create_item():
	if frappe.db.exists("Item", DEMO_ITEM):
		return
	item_group = frappe.db.get_value("Item Group", {"is_group": 0}, "name")
	stock_uom = frappe.db.get_value("UOM", {}, "name")
	frappe.get_doc(
		{
			"doctype": "Item",
			"item_code": DEMO_ITEM,
			"item_name": "Plano de internet Fibra 500 Mbps (Demo)",
			"item_group": item_group,
			"stock_uom": stock_uom,
			"is_stock_item": 0,
			"include_item_in_manufacturing": 0,
		}
	).insert(ignore_permissions=True)


def _create_plan(company):
	if not frappe.db.exists("Subscription Plan", DEMO_PLAN):
		frappe.get_doc(
			{
				"doctype": "Subscription Plan",
				"plan_name": DEMO_PLAN,
				"item": DEMO_ITEM,
				"currency": company.default_currency,
				"price_determination": "Fixed Rate",
				"cost": 109.90,
				"billing_interval": "Month",
				"billing_interval_count": 1,
				"cost_center": company.cost_center,
			}
		).insert(ignore_permissions=True)
	frappe.db.set_value("Customer", DEMO_CUSTOMER, "custom_subscription_plan", DEMO_PLAN)


def _create_subscription(company):
	existing = frappe.db.get_value(
		"Subscription", {"party_type": "Customer", "party": DEMO_CUSTOMER}, "name"
	)
	if existing:
		return existing
	doc = frappe.get_doc(
		{
			"doctype": "Subscription",
			"party_type": "Customer",
			"party": DEMO_CUSTOMER,
			"company": company.name,
			"start_date": "2026-01-15",
			"generate_invoice_at": "Beginning of the current subscription period",
			"submit_invoice": 1,
			"cost_center": company.cost_center,
			"plans": [{"plan": DEMO_PLAN, "qty": 1}],
		}
	)
	doc.insert(ignore_permissions=True)
	return doc.name


def _create_invoice(company, reference, posting_date, due_date):
	existing = frappe.db.get_value(
		"Sales Invoice", {"customer": DEMO_CUSTOMER, "po_no": reference, "docstatus": ["<", 2]}, "name"
	)
	if existing:
		return frappe.get_doc("Sales Invoice", existing)

	doc = frappe.get_doc(
		{
			"doctype": "Sales Invoice",
			"company": company.name,
			"customer": DEMO_CUSTOMER,
			"posting_date": posting_date,
			"set_posting_time": 1,
			"due_date": due_date,
			"po_no": reference,
			"currency": company.default_currency,
			"debit_to": company.default_receivable_account,
			"remarks": "DADOS FICTÍCIOS PARA DEMONSTRAÇÃO DO SOL PROVEDOR",
			"items": [
				{
					"item_code": DEMO_ITEM,
					"qty": 1,
					"rate": 109.90,
					"income_account": company.default_income_account,
					"cost_center": company.cost_center,
				}
			],
		}
	)
	doc.insert(ignore_permissions=True)
	doc.submit()
	return doc


def _create_payment(invoice):
	from erpnext.accounts.doctype.payment_entry.payment_entry import get_payment_entry

	payment = get_payment_entry("Sales Invoice", invoice.name)
	payment.reference_no = f"PAG-{invoice.po_no}"
	payment.reference_date = getdate(invoice.due_date)
	payment.remarks = "PAGAMENTO FICTÍCIO PARA DEMONSTRAÇÃO DO SOL PROVEDOR"
	payment.insert(ignore_permissions=True)
	payment.submit()


def _create_issue(company):
	existing = frappe.db.get_value(
		"Issue", {"customer": DEMO_CUSTOMER, "subject": "Sinal óptico instável (Demonstração)"}, "name"
	)
	if existing:
		return existing
	doc = frappe.get_doc(
		{
			"doctype": "Issue",
			"subject": "Sinal óptico instável (Demonstração)",
			"customer": DEMO_CUSTOMER,
			"company": company.name,
			"priority": "High",
			"description": "Dado fictício: cliente relata oscilações no acesso de fibra.",
		}
	)
	doc.insert(ignore_permissions=True)
	return doc.name


def _create_service_order(company):
	existing = frappe.db.get_value(
		"Maintenance Visit", {"customer": DEMO_CUSTOMER, "mntc_date": "2026-08-18"}, "name"
	)
	if existing:
		return existing
	service_person = "Técnico Demonstração"
	if not frappe.db.exists("Sales Person", service_person):
		root_sales_person = frappe.db.get_value("Sales Person", {"is_group": 1}, "name")
		frappe.get_doc(
			{
				"doctype": "Sales Person",
				"sales_person_name": service_person,
				"parent_sales_person": root_sales_person,
				"is_group": 0,
			}
		).insert(ignore_permissions=True)
	doc = frappe.get_doc(
		{
			"doctype": "Maintenance Visit",
			"customer": DEMO_CUSTOMER,
			"company": company.name,
			"mntc_date": "2026-08-18",
			"mntc_time": "09:30:00",
			"maintenance_type": "Breakdown",
			"completion_status": "Partially Completed",
			"customer_feedback": "Dado fictício para teste do painel de atendimentos.",
			"purposes": [
				{
					"item_code": DEMO_ITEM,
					"service_person": service_person,
					"work_done": "Verificar potência óptica, conectores e estabilidade da ONU.",
				}
			],
		}
	)
	doc.insert(ignore_permissions=True)
	return doc.name
