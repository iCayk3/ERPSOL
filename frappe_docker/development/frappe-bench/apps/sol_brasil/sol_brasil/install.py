import json

import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields
from frappe.custom.doctype.property_setter.property_setter import make_property_setter


CUSTOM_FIELDS = {
	"Customer": [
		{
			"fieldname": "custom_brazilian_tax_section",
			"fieldtype": "Section Break",
			"label": "Documentos e identificação",
			"insert_after": "territory",
		},
		{
			"fieldname": "custom_person_type",
			"fieldtype": "Select",
			"label": "Tipo de pessoa",
			"options": "Pessoa Jurídica\nPessoa Física",
			"default": "Pessoa Jurídica",
			"reqd": 0,
			"hidden": 1,
			"in_standard_filter": 1,
			"insert_after": "tax_id",
		},
		{
			"fieldname": "custom_tax_document",
			"fieldtype": "Data",
			"label": "CPF",
			"reqd": 0,
			"allow_in_quick_entry": 1,
			"unique": 1,
			"in_standard_filter": 1,
			"insert_after": "custom_brazilian_tax_section",
		},
		{
			"fieldname": "custom_identity_document",
			"fieldtype": "Data",
			"label": "RG",
			"depends_on": "eval:doc.customer_type == 'Individual'",
			"insert_after": "custom_tax_document",
		},
		{
			"fieldname": "custom_birth_date",
			"fieldtype": "Date",
			"label": "Nascimento",
			"depends_on": "eval:doc.customer_type == 'Individual'",
			"insert_after": "custom_identity_document",
		},
		{
			"fieldname": "custom_icms_taxpayer_type",
			"fieldtype": "Select",
			"label": "Indicador de contribuinte do ICMS",
			"options": "Não contribuinte\nContribuinte do ICMS\nContribuinte isento",
			"default": "Não contribuinte",
			"insert_after": "custom_municipal_registration",
		},
		{
			"fieldname": "custom_brazilian_tax_column",
			"fieldtype": "Column Break",
			"insert_after": "custom_icms_taxpayer_type",
		},
		{
			"fieldname": "custom_legal_name",
			"fieldtype": "Data",
			"label": "Razão social",
			"depends_on": "eval:doc.customer_type == 'Company'",
			"mandatory_depends_on": "eval:doc.customer_type == 'Company'",
			"insert_after": "custom_brazilian_tax_column",
		},
		{
			"fieldname": "custom_trade_name",
			"fieldtype": "Data",
			"label": "Nome fantasia",
			"depends_on": "eval:doc.customer_type == 'Company'",
			"insert_after": "custom_legal_name",
		},
		{
			"fieldname": "custom_state_registration",
			"fieldtype": "Data",
			"label": "Inscrição estadual",
			"depends_on": "eval:doc.customer_type == 'Company'",
			"insert_after": "custom_birth_date",
		},
		{
			"fieldname": "custom_municipal_registration",
			"fieldtype": "Data",
			"label": "Inscrição municipal",
			"depends_on": "eval:doc.customer_type == 'Company'",
			"insert_after": "custom_state_registration",
		},
		{
			"fieldname": "custom_provider_tab",
			"fieldtype": "Tab Break",
			"label": "Provedor",
			"insert_after": "contact_and_address_tab",
		},
		{
			"fieldname": "custom_provider_access_section",
			"fieldtype": "Section Break",
			"label": "Acesso PPPoE e contrato",
			"insert_after": "custom_provider_tab",
		},
		{
			"fieldname": "custom_connection_status",
			"fieldtype": "Select",
			"label": "Situação da conexão",
			"options": "Aguardando instalação\nAtivo\nSuspenso\nBloqueado\nCancelado",
			"default": "Aguardando instalação",
			"in_list_view": 1,
			"in_standard_filter": 1,
			"insert_after": "custom_provider_access_column",
		},
		{
			"fieldname": "custom_subscription_plan",
			"fieldtype": "Link",
			"label": "Plano de internet",
			"options": "Subscription Plan",
			"insert_after": "custom_connection_status",
		},
		{
			"fieldname": "custom_activation_date",
			"fieldtype": "Date",
			"label": "Data de ativação",
			"insert_after": "custom_subscription_plan",
		},
		{
			"fieldname": "custom_pppoe_username",
			"fieldtype": "Data",
			"label": "Usuário PPPoE",
			"unique": 1,
			"in_standard_filter": 1,
			"insert_after": "custom_provider_access_section",
		},
		{
			"fieldname": "custom_pppoe_password",
			"fieldtype": "Password",
			"label": "Senha PPPoE",
			"insert_after": "custom_pppoe_username",
		},
		{
			"fieldname": "custom_linked_subscription",
			"fieldtype": "Link",
			"label": "Contrato vinculado",
			"options": "Subscription",
			"description": "Contrato que controla o plano e a cobrança deste acesso.",
			"insert_after": "custom_pppoe_password",
		},
		{
			"fieldname": "custom_change_contract",
			"fieldtype": "Button",
			"label": "Consultar ou trocar contrato",
			"insert_after": "custom_linked_subscription",
		},
		{
			"fieldname": "custom_provider_access_column",
			"fieldtype": "Column Break",
			"insert_after": "custom_change_contract",
		},
		{
			"fieldname": "custom_provider_network_section",
			"fieldtype": "Section Break",
			"label": "Equipamentos e rede óptica",
			"insert_after": "custom_activation_date",
		},
		{
			"fieldname": "custom_ipv4_address",
			"fieldtype": "Data",
			"label": "Endereço IPv4",
			"insert_after": "custom_provider_network_section",
		},
		{
			"fieldname": "custom_mac_address",
			"fieldtype": "Data",
			"label": "Endereço MAC",
			"insert_after": "custom_ipv4_address",
		},
		{
			"fieldname": "custom_vlan_id",
			"fieldtype": "Int",
			"label": "VLAN",
			"insert_after": "custom_mac_address",
		},
		{
			"fieldname": "custom_optical_splitter",
			"fieldtype": "Data",
			"label": "Splitter óptico",
			"insert_after": "custom_vlan_id",
		},
		{
			"fieldname": "custom_installation_box",
			"fieldtype": "Data",
			"label": "Caixa de atendimento (CTO/NAP)",
			"insert_after": "custom_optical_splitter",
		},
		{
			"fieldname": "custom_provider_network_column",
			"fieldtype": "Column Break",
			"insert_after": "custom_installation_box",
		},
		{
			"fieldname": "custom_olt",
			"fieldtype": "Data",
			"label": "OLT",
			"insert_after": "custom_provider_network_column",
		},
		{
			"fieldname": "custom_olt_slot",
			"fieldtype": "Data",
			"label": "Slot da OLT",
			"insert_after": "custom_olt",
		},
		{
			"fieldname": "custom_pon",
			"fieldtype": "Data",
			"label": "PON",
			"insert_after": "custom_olt_slot",
		},
		{
			"fieldname": "custom_pon_port",
			"fieldtype": "Data",
			"label": "Porta PON",
			"insert_after": "custom_pon",
		},
		{
			"fieldname": "custom_onu_serial",
			"fieldtype": "Data",
			"label": "ONU / número de série",
			"insert_after": "custom_pon_port",
		},
		{
			"fieldname": "custom_onu_id",
			"fieldtype": "Data",
			"label": "ID da ONU/ONT",
			"insert_after": "custom_onu_serial",
		},
		{
			"fieldname": "custom_onu_model",
			"fieldtype": "Data",
			"label": "Modelo da ONU/ONT",
			"insert_after": "custom_onu_id",
		},
		{
			"fieldname": "custom_onu_rx_signal",
			"fieldtype": "Float",
			"label": "Sinal RX (dBm)",
			"precision": "2",
			"insert_after": "custom_onu_model",
		},
		{
			"fieldname": "custom_onu_tx_signal",
			"fieldtype": "Float",
			"label": "Sinal TX (dBm)",
			"precision": "2",
			"insert_after": "custom_onu_rx_signal",
		},
		{
			"fieldname": "custom_network_notes",
			"fieldtype": "Small Text",
			"label": "Observações técnicas da rede",
			"insert_after": "custom_onu_tx_signal",
		},
		{
			"fieldname": "custom_contracts_tab",
			"fieldtype": "Tab Break",
			"label": "Contratos",
			"insert_after": "custom_network_notes",
		},
		{
			"fieldname": "custom_contracts_panel",
			"fieldtype": "HTML",
			"label": "Contratos do cliente",
			"insert_after": "custom_contracts_tab",
		},
		{
			"fieldname": "custom_financial_tab",
			"fieldtype": "Tab Break",
			"label": "Financeiro",
			"insert_after": "custom_contracts_panel",
		},
		{
			"fieldname": "custom_financial_panel",
			"fieldtype": "HTML",
			"label": "Boletos do cliente",
			"insert_after": "custom_financial_tab",
		},
		{
			"fieldname": "custom_service_tab",
			"fieldtype": "Tab Break",
			"label": "Atendimentos",
			"insert_after": "custom_financial_panel",
		},
		{
			"fieldname": "custom_service_panel",
			"fieldtype": "HTML",
			"label": "Atendimentos e ordens de serviço",
			"insert_after": "custom_service_tab",
		},
	],
	"Lead": [
		{
			"fieldname": "custom_provider_interest_section",
			"fieldtype": "Section Break",
			"label": "Interesse no provedor",
			"insert_after": "request_type",
		},
		{
			"fieldname": "custom_tax_document",
			"fieldtype": "Data",
			"label": "CPF / CNPJ",
			"insert_after": "custom_provider_interest_section",
		},
		{
			"fieldname": "custom_interest_plan",
			"fieldtype": "Link",
			"label": "Plano de interesse",
			"options": "Subscription Plan",
			"insert_after": "custom_tax_document",
		},
		{
			"fieldname": "custom_installation_region",
			"fieldtype": "Data",
			"label": "Bairro / região da instalação",
			"insert_after": "custom_interest_plan",
		},
	]
}


def setup_customer_fields():
	create_custom_fields(CUSTOM_FIELDS, update=True)
	frappe.db.sql(
		"""
		UPDATE `tabCustomer`
		SET custom_tax_document = tax_id
		WHERE COALESCE(custom_tax_document, '') = '' AND COALESCE(tax_id, '') != ''
		"""
	)
	make_property_setter("Customer", None, "module", "SOL Brasil", "Data")
	make_property_setter("Customer", "tax_id", "label", "CPF / CNPJ", "Data")
	make_property_setter("Customer", "tax_id", "description", "Informe um CPF ou CNPJ válido.", "Text")
	make_property_setter("Customer", "tax_id", "hidden", 1, "Check")
	make_property_setter("Customer", "tax_id", "reqd", 0, "Check")
	make_property_setter("Customer", "default_currency", "label", "Moeda de cobrança", "Data")
	make_property_setter("Customer", "default_bank_account", "label", "Conta bancária da empresa", "Data")
	backfill_customer_contract_links()
	reorder_customer_relationships_tab()


def backfill_customer_contract_links():
	customers = frappe.get_all(
		"Subscription",
		filters={"party_type": "Customer", "status": ["not in", ["Cancelled", "Completed"]]},
		fields=["party", "name"],
		order_by="start_date desc, modified desc",
	)
	linked = set()
	for row in customers:
		if not row.party or row.party in linked:
			continue
		linked.add(row.party)
		if not frappe.db.get_value("Customer", row.party, "custom_linked_subscription"):
			frappe.db.set_value(
				"Customer", row.party, "custom_linked_subscription", row.name, update_modified=False
			)


def reorder_customer_relationships_tab():
	"""Move o bloco completo de Relacionamentos para depois de Atendimentos."""
	frappe.clear_cache(doctype="Customer")
	fields = list(frappe.get_meta("Customer").fields)
	fieldnames = [field.fieldname for field in fields]
	if "connections_tab" not in fieldnames or "custom_service_panel" not in fieldnames:
		return

	start = fieldnames.index("connections_tab")
	end = len(fields)
	for index in range(start + 1, len(fields)):
		if fields[index].fieldtype == "Tab Break":
			end = index
			break

	relationships_block = fieldnames[start:end]
	remaining = fieldnames[:start] + fieldnames[end:]
	insert_at = remaining.index("custom_service_panel") + 1
	new_order = remaining[:insert_at] + relationships_block + remaining[insert_at:]
	make_property_setter("Customer", None, "field_order", json.dumps(new_order), "Text")
	frappe.clear_cache(doctype="Customer")
	make_property_setter("Customer", "basic_info", "label", "Cadastro do cliente", "Data")
	make_property_setter("Customer", "customer_type", "label", "Tipo de cliente", "Data")
	make_property_setter("Customer", "territory", "label", "Área de atendimento", "Data")
	make_property_setter("Customer", "contact_and_address_tab", "label", "Endereço e contato", "Data")
	make_property_setter("Customer", "accounting_tab", "label", "Configuração financeira", "Data")
	make_property_setter("Customer", "tax_tab", "label", "Fiscal", "Data")
	make_property_setter("Customer", "settings_tab", "label", "Regras comerciais", "Data")
	make_property_setter("Customer", "sales_team_tab", "label", "Equipe responsável", "Data")
	make_property_setter("Customer", "sales_team_tab", "hidden", 1, "Check")
	make_property_setter("Customer", "portal_users_tab", "label", "Acesso ao portal", "Data")
	make_property_setter("Customer", "more_info_tab", "label", "Mais informações", "Data")
	make_property_setter("Customer", "connections_tab", "label", "Relacionamentos", "Data")
	frappe.clear_cache(doctype="Customer")


def after_install():
    setup_customer_fields()
    from sol_brasil.workspace import sync_provider_workspaces

    sync_provider_workspaces()


def after_migrate():
    setup_customer_fields()
    from sol_brasil.workspace import sync_provider_workspaces

    sync_provider_workspaces()
