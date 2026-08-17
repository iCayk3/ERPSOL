import frappe


def _get_eligible_contract(lead_name):
	settings = frappe.get_single("Configurações do Provedor")
	contracts = frappe.get_all(
		"Contrato Preliminar",
		filters={"lead": lead_name, "contract_status": ["not in", ["Cancelado", "Convertido"]]},
		fields=["name", "contract_flow", "contract_status", "subscription_plan", "start_date", "payment_date"],
		order_by="modified desc",
	)
	for contract in contracts:
		if contract.contract_flow == "Pós-pagamento" and contract.contract_status == "Pronto para conversão":
			return contract
		if contract.contract_flow == "Pré-pagamento":
			if not settings.require_prepaid_payment or contract.contract_status == "Pago":
				return contract
	frappe.throw(
		"Antes de converter este Lead, crie um contrato preliminar válido. "
		"No pré-pagamento, confirme também o recebimento quando essa exigência estiver ativa."
	)


@frappe.whitelist()
def make_customer(source_name):
	from erpnext.crm.doctype.lead.lead import _make_customer

	lead = frappe.get_doc("Lead", source_name)
	lead.check_permission("read")
	contract = _get_eligible_contract(source_name)
	target = _make_customer(source_name)
	target.custom_tax_document = lead.custom_tax_document
	target.tax_id = lead.custom_tax_document
	target.custom_subscription_plan = lead.custom_interest_plan
	target.mobile_no = lead.mobile_no or lead.phone
	target.email_id = lead.email_id
	target.flags.sol_preliminary_contract = contract.name
	return target


@frappe.whitelist()
def get_contract_configuration():
	settings = frappe.get_single("Configurações do Provedor")
	return {
		"lead_contract_flow": settings.lead_contract_flow or "Permitir escolha no Lead",
		"require_prepaid_payment": bool(settings.require_prepaid_payment),
	}


@frappe.whitelist()
def should_return_to_customer():
	return bool(frappe.db.get_single_value("Configurações do Provedor", "return_to_customer_after_save"))


def finalize_lead_conversion(doc, method=None):
	if not doc.lead_name:
		return
	contract = _get_eligible_contract(doc.lead_name)
	company = frappe.defaults.get_user_default("Company") or frappe.db.get_single_value("Global Defaults", "default_company")
	subscription = frappe.get_doc({
		"doctype": "Subscription",
		"party_type": "Customer",
		"party": doc.name,
		"company": company,
		"start_date": contract.start_date,
		"generate_invoice_at": (
			"Beginning of the current subscription period"
			if contract.contract_flow == "Pré-pagamento"
			else "End of the current subscription period"
		),
		"plans": [{"plan": contract.subscription_plan, "qty": 1}],
	})
	subscription.insert(ignore_permissions=True)
	frappe.db.set_value("Customer", doc.name, {
		"custom_linked_subscription": subscription.name,
		"custom_subscription_plan": contract.subscription_plan,
	})
	frappe.db.set_value("Contrato Preliminar", contract.name, {
		"customer": doc.name,
		"converted_subscription": subscription.name,
		"contract_status": "Convertido",
	})
	frappe.db.set_value("Lead", doc.lead_name, "status", "Converted")


@frappe.whitelist()
def create_from_customer_quick_entry(data):
	values = frappe.parse_json(data)
	name = (values.get("customer_name") or "").strip()
	mobile = (values.get("mobile_number") or "").strip()
	email = (values.get("email_address") or "").strip()
	if not name:
		frappe.throw("Informe o nome do futuro cliente.")
	if not (mobile or email):
		frappe.throw("Informe pelo menos o celular ou o e-mail para contato.")

	is_company = values.get("customer_type") == "Company"
	lead = frappe.get_doc(
		{
			"doctype": "Lead",
			"first_name": name if not is_company else None,
			"company_name": name if is_company else None,
			"mobile_no": mobile,
			"email_id": email,
			"custom_tax_document": values.get("custom_tax_document"),
			"custom_installation_region": values.get("city"),
			"status": "Lead",
		}
	)
	lead.insert()
	return lead
