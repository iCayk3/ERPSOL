import json

import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields
from frappe.custom.doctype.property_setter.property_setter import make_property_setter


CUSTOM_FIELDS = {
	"Customer": [
		{
			"fieldname": "custom_customer_code",
			"fieldtype": "Data",
			"label": "Código",
			"read_only": 1,
			"unique": 1,
			"in_list_view": 1,
			"in_standard_filter": 1,
			"insert_after": "customer_name",
		},
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
			"insert_after": "custom_internet_points_panel",
		},
		{
			"fieldname": "custom_internet_points_panel",
			"fieldtype": "HTML",
			"label": "Pontos de internet",
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
			"fieldtype": "Link",
			"label": "OLT",
			"options": "OLT",
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
			"fieldname": "custom_onu_id_type",
			"fieldtype": "Select",
			"label": "Tipo de identificador",
			"options": "MAC\nLOID\nONU_NUMBER\nONU_NAME",
			"default": "MAC",
			"insert_after": "custom_onu_id",
		},
		{
			"fieldname": "custom_onu_auth_type",
			"fieldtype": "Select",
			"label": "Autenticação da ONU",
			"options": "MAC\nLOID\nLOIDONCEON",
			"default": "MAC",
			"insert_after": "custom_onu_id_type",
		},
		{
			"fieldname": "custom_onu_auth_password",
			"fieldtype": "Password",
			"label": "Senha LOID",
			"depends_on": "eval:doc.custom_onu_auth_type != 'MAC'",
			"insert_after": "custom_onu_auth_type",
		},
		{
			"fieldname": "custom_onu_number",
			"fieldtype": "Int",
			"label": "Número da ONU na PON",
			"description": "Código ONUNO entre 1 e 512.",
			"insert_after": "custom_onu_auth_password",
		},
		{
			"fieldname": "custom_onu_model",
			"fieldtype": "Data",
			"label": "Modelo da ONU/ONT",
			"insert_after": "custom_onu_number",
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
			"fieldname": "custom_onu_signal_status",
			"fieldtype": "Data",
			"label": "Classificação do sinal",
			"read_only": 1,
			"insert_after": "custom_onu_tx_signal",
		},
		{
			"fieldname": "custom_onu_signal_checked_at",
			"fieldtype": "Datetime",
			"label": "Última consulta de sinal",
			"read_only": 1,
			"insert_after": "custom_onu_signal_status",
		},
		{
			"fieldname": "custom_network_notes",
			"fieldtype": "Small Text",
			"label": "Observações técnicas da rede",
			"insert_after": "custom_onu_signal_checked_at",
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
	],
	"Sales Invoice": [
		{
			"fieldname": "custom_billing_reference_section",
			"fieldtype": "Section Break",
			"label": "Referência do faturamento",
			"insert_after": "due_date",
		},
		{
			"fieldname": "custom_billing_reference_month",
			"fieldtype": "Data",
			"label": "Mês de referência",
			"description": "Mês do serviço faturado no formato AAAA-MM. Não deve mudar em renegociações.",
			"read_only": 1,
			"in_standard_filter": 1,
			"insert_after": "custom_billing_reference_section",
		},
		{
			"fieldname": "custom_original_due_date",
			"fieldtype": "Date",
			"label": "Vencimento original",
			"read_only": 1,
			"insert_after": "custom_billing_reference_month",
		},
		{
			"fieldname": "custom_renegotiated",
			"fieldtype": "Check",
			"label": "Renegociado",
			"read_only": 1,
			"insert_after": "custom_original_due_date",
		},
		{
			"fieldname": "custom_waive_interest_penalty",
			"fieldtype": "Check",
			"label": "Zerar juros e multa",
			"read_only": 1,
			"insert_after": "custom_renegotiated",
		},
		{
			"fieldname": "custom_negotiated_amount",
			"fieldtype": "Currency",
			"label": "Valor negociado",
			"description": "Valor acordado para cobrança. Não altera o faturamento original.",
			"read_only": 1,
			"insert_after": "custom_waive_interest_penalty",
		},
		{
			"fieldname": "custom_renegotiation_notes",
			"fieldtype": "Small Text",
			"label": "Observações da renegociação",
			"read_only": 1,
			"insert_after": "custom_negotiated_amount",
		},
	],
	"Subscription Plan": [
		{"fieldname": "custom_access_configuration_section", "fieldtype": "Section Break", "label": "Configuração técnica do acesso", "insert_after": "billing_interval_count"},
		{"fieldname": "custom_download_mbps", "fieldtype": "Int", "label": "Download (Mbps)", "non_negative": 1, "insert_after": "custom_access_configuration_section"},
		{"fieldname": "custom_upload_mbps", "fieldtype": "Int", "label": "Upload (Mbps)", "non_negative": 1, "insert_after": "custom_download_mbps"},
		{"fieldname": "custom_access_configuration_column", "fieldtype": "Column Break", "insert_after": "custom_upload_mbps"},
		{"fieldname": "custom_session_limit", "fieldtype": "Int", "label": "Limite de sessões simultâneas", "default": "1", "insert_after": "custom_access_configuration_column"},
		{"fieldname": "custom_accounting_interval", "fieldtype": "Int", "label": "Intervalo de accounting (s)", "default": "300", "description": "Intervalo entre atualizações de consumo enviadas pelo concentrador.", "insert_after": "custom_session_limit"},
		{"fieldname": "custom_overdue_policy_section", "fieldtype": "Section Break", "label": "Política de redução por atraso", "insert_after": "custom_accounting_interval"},
		{"fieldname": "custom_enable_overdue_reduction", "fieldtype": "Check", "label": "Reduzir banda antes do bloqueio", "default": "0", "description": "Opcional. Se desativado, este plano mantém a velocidade normal até o bloqueio.", "insert_after": "custom_overdue_policy_section"},
		{"fieldname": "custom_reduce_after_days", "fieldtype": "Int", "label": "Reduzir após quantos dias de atraso", "default": "1", "depends_on": "custom_enable_overdue_reduction", "insert_after": "custom_enable_overdue_reduction"},
		{"fieldname": "custom_overdue_policy_column", "fieldtype": "Column Break", "insert_after": "custom_reduce_after_days"},
		{"fieldname": "custom_download_reduction_percent", "fieldtype": "Percent", "label": "Redução do download (%)", "default": "50", "depends_on": "custom_enable_overdue_reduction", "insert_after": "custom_overdue_policy_column"},
		{"fieldname": "custom_upload_reduction_percent", "fieldtype": "Percent", "label": "Redução do upload (%)", "default": "50", "depends_on": "custom_enable_overdue_reduction", "insert_after": "custom_download_reduction_percent"},
		{"fieldname": "custom_radius_network_section", "fieldtype": "Section Break", "label": "Endereçamento e políticas RADIUS", "insert_after": "custom_upload_reduction_percent"},
		{"fieldname": "custom_ipv4_pool", "fieldtype": "Data", "label": "Pool IPv4", "insert_after": "custom_radius_network_section"},
		{"fieldname": "custom_ipv6_pool", "fieldtype": "Data", "label": "Pool IPv6", "insert_after": "custom_ipv4_pool"},
		{"fieldname": "custom_radius_network_column", "fieldtype": "Column Break", "insert_after": "custom_ipv6_pool"},
		{"fieldname": "custom_filter_id", "fieldtype": "Data", "label": "Filter-Id", "insert_after": "custom_radius_network_column"},
		{"fieldname": "custom_mikrotik_rate_limit", "fieldtype": "Data", "label": "Mikrotik-Rate-Limit", "read_only": 1, "description": "Gerado automaticamente a partir de upload e download.", "insert_after": "custom_filter_id"},
		{"fieldname": "custom_radius_attributes", "fieldtype": "Code", "label": "Atributos RADIUS adicionais", "options": "JSON", "description": "JSON com atributos técnicos adicionais. Não inclua senhas ou segredos.", "insert_after": "custom_mikrotik_rate_limit"},
	],
	"Subscription": [
		{
			"fieldname": "custom_installation_section",
			"fieldtype": "Section Break",
			"label": "Local de instalação",
			"insert_after": "party",
		},
		{
			"fieldname": "custom_installation_address",
			"fieldtype": "Link",
			"label": "Endereço de instalação",
			"options": "Address",
			"description": "Selecione um dos endereços cadastrados na ficha do cliente.",
			"insert_after": "custom_installation_section",
		},
		{"fieldname": "custom_provider_tab", "fieldtype": "Tab Break", "label": "Provedor", "insert_after": "plans"},
		{"fieldname": "custom_access_section", "fieldtype": "Section Break", "label": "Ponto e acesso PPPoE", "insert_after": "custom_provider_tab"},
		{"fieldname": "custom_internet_plan", "fieldtype": "Link", "label": "Plano de internet", "options": "Subscription Plan", "read_only": 1, "insert_after": "custom_access_section"},
		{"fieldname": "custom_pppoe_username", "fieldtype": "Data", "label": "Usuário PPPoE", "unique": 1, "in_standard_filter": 1, "insert_after": "custom_internet_plan"},
		{"fieldname": "custom_pppoe_password", "fieldtype": "Password", "label": "Senha PPPoE", "insert_after": "custom_pppoe_username"},
		{"fieldname": "custom_access_column", "fieldtype": "Column Break", "insert_after": "custom_pppoe_password"},
		{"fieldname": "custom_connection_status", "fieldtype": "Select", "label": "Situação da conexão", "options": "Aguardando instalação\nAtivo\nSuspenso\nBloqueado\nCancelado", "default": "Aguardando instalação", "read_only": 1, "in_list_view": 1, "in_standard_filter": 1, "insert_after": "custom_access_column"},
		{"fieldname": "custom_activation_date", "fieldtype": "Date", "label": "Data de ativação", "insert_after": "custom_connection_status"},
		{"fieldname": "custom_bandwidth_reduced", "fieldtype": "Check", "label": "Banda reduzida por atraso", "read_only": 1, "insert_after": "custom_activation_date"},
		{"fieldname": "custom_effective_download_mbps", "fieldtype": "Int", "label": "Download efetivo (Mbps)", "read_only": 1, "insert_after": "custom_bandwidth_reduced"},
		{"fieldname": "custom_effective_upload_mbps", "fieldtype": "Int", "label": "Upload efetivo (Mbps)", "read_only": 1, "insert_after": "custom_effective_download_mbps"},
		{"fieldname": "custom_effective_rate_limit", "fieldtype": "Data", "label": "Rate-Limit efetivo", "read_only": 1, "insert_after": "custom_effective_upload_mbps"},
		{"fieldname": "custom_radius_provisioning_state", "fieldtype": "Select", "label": "Provisionamento RADIUS", "options": "Não provisionado\nPendente\nSincronizado\nErro\nDesativado", "default": "Não provisionado", "read_only": 1, "in_standard_filter": 1, "insert_after": "custom_effective_rate_limit"},
		{"fieldname": "custom_radius_provisioning_version", "fieldtype": "Int", "label": "Versão RADIUS", "default": "0", "read_only": 1, "insert_after": "custom_radius_provisioning_state"},
		{"fieldname": "custom_radius_last_sync", "fieldtype": "Datetime", "label": "Última sincronização RADIUS", "read_only": 1, "insert_after": "custom_radius_provisioning_version"},
		{"fieldname": "custom_radius_last_error", "fieldtype": "Small Text", "label": "Último erro RADIUS", "read_only": 1, "insert_after": "custom_radius_last_sync"},
		{"fieldname": "custom_radius_snapshot_hash", "fieldtype": "Data", "label": "Hash da configuração RADIUS", "hidden": 1, "read_only": 1, "insert_after": "custom_radius_last_error"},
		{"fieldname": "custom_network_section", "fieldtype": "Section Break", "label": "Equipamentos e rede óptica", "insert_after": "custom_radius_snapshot_hash"},
		{"fieldname": "custom_ipv4_address", "fieldtype": "Data", "label": "Endereço IPv4", "insert_after": "custom_network_section"},
		{"fieldname": "custom_mac_address", "fieldtype": "Data", "label": "Endereço MAC", "insert_after": "custom_ipv4_address"},
		{"fieldname": "custom_vlan_id", "fieldtype": "Int", "label": "VLAN", "insert_after": "custom_mac_address"},
		{"fieldname": "custom_optical_splitter", "fieldtype": "Data", "label": "Splitter óptico", "insert_after": "custom_vlan_id"},
		{"fieldname": "custom_installation_box", "fieldtype": "Data", "label": "Caixa de atendimento (legado)", "hidden": 1, "insert_after": "custom_optical_splitter"},
		{"fieldname": "custom_network_column", "fieldtype": "Column Break", "insert_after": "custom_installation_box"},
		{"fieldname": "custom_olt", "fieldtype": "Link", "label": "OLT", "options": "OLT", "insert_after": "custom_network_column"},
		{"fieldname": "custom_olt_slot", "fieldtype": "Data", "label": "Slot da OLT (legado)", "hidden": 1, "insert_after": "custom_olt"},
		{"fieldname": "custom_olt_slot_select", "fieldtype": "Select", "label": "Slot da OLT", "insert_after": "custom_olt_slot"},
		{"fieldname": "custom_pon", "fieldtype": "Data", "label": "PON (legado)", "hidden": 1, "insert_after": "custom_olt_slot_select"},
		{"fieldname": "custom_pon_select", "fieldtype": "Select", "label": "PON", "insert_after": "custom_pon"},
		{"fieldname": "custom_installation_box_link", "fieldtype": "Link", "label": "Caixa de atendimento (CTO/NAP)", "options": "Caixa de Atendimento", "insert_after": "custom_pon_select"},
		{"fieldname": "custom_cto_port", "fieldtype": "Select", "label": "Porta da CTO", "description": "Somente portas disponíveis desta CTO são exibidas.", "insert_after": "custom_installation_box_link"},
		{"fieldname": "custom_pon_port", "fieldtype": "Data", "label": "Porta PON", "hidden": 1, "insert_after": "custom_cto_port"},
		{"fieldname": "custom_onu_serial", "fieldtype": "Data", "label": "ONU / número de série", "insert_after": "custom_pon_port"},
		{"fieldname": "custom_onu_id", "fieldtype": "Data", "label": "ID da ONU/ONT", "insert_after": "custom_onu_serial"},
		{"fieldname": "custom_onu_id_type", "fieldtype": "Select", "label": "Tipo de identificador", "options": "MAC\nLOID\nONU_NUMBER\nONU_NAME", "default": "MAC", "insert_after": "custom_onu_id"},
		{"fieldname": "custom_onu_auth_type", "fieldtype": "Select", "label": "Autenticação da ONU", "options": "MAC\nLOID\nLOIDONCEON", "default": "MAC", "insert_after": "custom_onu_id_type"},
		{"fieldname": "custom_onu_auth_password", "fieldtype": "Password", "label": "Senha LOID", "depends_on": "eval:doc.custom_onu_auth_type != 'MAC'", "insert_after": "custom_onu_auth_type"},
		{"fieldname": "custom_onu_number", "fieldtype": "Int", "label": "Número da ONU na PON", "description": "Código ONUNO entre 1 e 512.", "insert_after": "custom_onu_auth_password"},
		{"fieldname": "custom_onu_model", "fieldtype": "Data", "label": "Modelo da ONU/ONT", "insert_after": "custom_onu_number"},
		{"fieldname": "custom_onu_rx_signal", "fieldtype": "Float", "label": "Sinal RX (dBm)", "precision": "2", "read_only": 1, "insert_after": "custom_onu_model"},
		{"fieldname": "custom_onu_tx_signal", "fieldtype": "Float", "label": "Sinal TX (dBm)", "precision": "2", "read_only": 1, "insert_after": "custom_onu_rx_signal"},
		{"fieldname": "custom_onu_signal_status", "fieldtype": "Data", "label": "Classificação do sinal", "read_only": 1, "insert_after": "custom_onu_tx_signal"},
		{"fieldname": "custom_onu_signal_checked_at", "fieldtype": "Datetime", "label": "Última consulta de sinal", "read_only": 1, "insert_after": "custom_onu_signal_status"},
		{"fieldname": "custom_network_notes", "fieldtype": "Small Text", "label": "Observações técnicas da rede", "insert_after": "custom_onu_signal_checked_at"},
		{"fieldname": "custom_details_tab", "fieldtype": "Tab Break", "label": "Detalhes", "insert_after": "custom_network_notes"},
	],
	"Issue": [
		{
			"fieldname": "custom_service_subject",
			"fieldtype": "Link",
			"label": "Assunto do atendimento",
			"options": "Assunto de Atendimento",
			"mandatory_depends_on": "eval:doc.customer",
			"in_standard_filter": 1,
			"insert_after": "subject",
		},
		{
			"fieldname": "custom_generated_service_order",
			"fieldtype": "Link",
			"label": "Ordem de serviço gerada",
			"options": "Maintenance Visit",
			"read_only": 1,
			"insert_after": "custom_service_subject",
		},
	],
	"Maintenance Visit": [
		{
			"fieldname": "custom_service_subject",
			"fieldtype": "Link",
			"label": "Assunto do atendimento",
			"options": "Assunto de Atendimento",
			"reqd": 1,
			"in_standard_filter": 1,
			"insert_after": "customer",
		},
		{
			"fieldname": "custom_origin_issue",
			"fieldtype": "Link",
			"label": "Atendimento de origem",
			"options": "Issue",
			"read_only": 1,
			"insert_after": "custom_service_subject",
		},
	],
	"Maintenance Visit Purpose": [
		{
			"fieldname": "custom_provider_service",
			"fieldtype": "Link",
			"label": "Serviço a executar",
			"options": "Servico do Provedor",
			"reqd": 1,
			"in_list_view": 1,
			"insert_after": "item_name",
		},
	],
	"Task Depends On": [
		{
			"fieldname": "custom_completed",
			"fieldtype": "Check",
			"label": "Concluído",
			"default": 0,
			"in_list_view": 1,
			"insert_after": "subject",
		},
		{
			"fieldname": "custom_open_task",
			"fieldtype": "Button",
			"label": "Abrir tarefa",
			"insert_after": "custom_completed",
		},
	],
}


DEFAULT_SERVICE_SUBJECTS = (
	("Sem conexão", "Cliente sem acesso à internet."),
	("Lentidão", "Baixa velocidade, latência ou instabilidade percebida."),
	("Instalação", "Instalação ou ativação de novo acesso."),
	("Mudança de endereço", "Transferência do ponto de instalação."),
	("Troca de equipamento", "Substituição de ONU, roteador ou equipamento relacionado."),
	("Financeiro", "Dúvidas ou solicitações relacionadas à cobrança."),
	("Cancelamento", "Solicitação relacionada ao cancelamento do serviço."),
	("Outros", "Assunto não classificado nas opções anteriores."),
)

DEFAULT_PROVIDER_SERVICES = (
	("Instalação de acesso", "Instalação e ativação do acesso do cliente."),
	("Visita técnica", "Diagnóstico técnico no endereço do cliente."),
	("Reparo de fibra", "Correção de rompimento, conectorização ou perda óptica."),
	("Configuração de roteador", "Configuração de Wi-Fi, roteamento e parâmetros do equipamento."),
	("Troca de ONU/ONT", "Substituição e provisionamento da ONU/ONT."),
	("Mudança de endereço", "Transferência física do ponto de instalação."),
	("Retirada de equipamento", "Recolhimento de equipamentos vinculados ao acesso."),
)


STANDARD_MASTER_RENAMES = {
	"Item Group": {
		"All Item Groups": "Todos os grupos de itens",
		"Consumable": "Consumíveis",
		"Demo Item Group": "Grupo de itens de demonstração",
		"Products": "Produtos",
		"Raw Material": "Matéria-prima",
		"Services": "Serviços",
		"Sub Assemblies": "Subconjuntos",
	},
	"Customer Group": {
		"All Customer Groups": "Todos os grupos de clientes",
		"Commercial": "Comercial",
		"Government": "Governo",
		"Individual": "Pessoa física",
		"Non Profit": "Sem fins lucrativos",
	},
	"Supplier Group": {
		"All Supplier Groups": "Todos os grupos de fornecedores",
		"Distributor": "Distribuidor",
		"Electrical": "Elétrico",
		"Hardware": "Equipamentos",
		"Local": "Local",
		"Pharmaceutical": "Farmacêutico",
		"Raw Material": "Matéria-prima",
		"Services": "Serviços",
	},
	"Territory": {
		"All Territories": "Todas as áreas de atendimento",
		"Brazil": "Brasil",
		"Rest Of The World": "Fora do Brasil",
	},
	"Sales Person": {
		"Sales Team": "Equipe comercial",
	},
	"Mode of Payment": {
		"Bank Draft": "Transferência bancária",
		"Cash": "Dinheiro",
		"Cheque": "Cheque",
		"Credit Card": "Cartão de crédito",
		"Wire Transfer": "Transferência eletrônica",
	},
	"Warehouse Type": {
		"Transit": "Trânsito",
	},
	"Price List": {
		"Standard Buying": "Compra padrão",
		"Standard Selling": "Venda padrão",
	},
	"Opportunity Type": {
		"Maintenance": "Manutenção",
		"Sales": "Venda",
		"Support": "Suporte",
	},
	"Market Segment": {
		"Lower Income": "Baixa renda",
		"Middle Income": "Média renda",
		"Upper Income": "Alta renda",
	},
	"Print Heading": {
		"Credit Note": "Nota de crédito",
		"Debit Note": "Nota de débito",
	},
	"Letter Head": {
		"Company Letterhead": "Papel timbrado da empresa",
		"Company Letterhead - Grey": "Papel timbrado da empresa - Cinza",
	},
	"Industry Type": {
		"Accounting": "Contabilidade",
		"Advertising": "Publicidade",
		"Aerospace": "Aeroespacial",
		"Agriculture": "Agricultura",
		"Airline": "Companhia aérea",
		"Apparel & Accessories": "Vestuário e acessórios",
		"Automotive": "Automotivo",
		"Banking": "Bancário",
		"Biotechnology": "Biotecnologia",
		"Broadcasting": "Radiodifusão",
		"Brokerage": "Corretagem",
		"Chemical": "Químico",
		"Computer": "Informática",
		"Consulting": "Consultoria",
		"Consumer Products": "Produtos de consumo",
		"Cosmetics": "Cosméticos",
		"Defense": "Defesa",
		"Department Stores": "Lojas de departamento",
		"Education": "Educação",
		"Electronics": "Eletrônicos",
		"Energy": "Energia",
		"Entertainment & Leisure": "Entretenimento e lazer",
		"Executive Search": "Recrutamento executivo",
		"Financial Services": "Serviços financeiros",
		"Food, Beverage & Tobacco": "Alimentos, bebidas e tabaco",
		"Grocery": "Mercearia",
		"Health Care": "Saúde",
		"Internet Publishing": "Publicação na internet",
		"Investment Banking": "Banco de investimento",
		"Legal": "Jurídico",
		"Manufacturing": "Indústria",
		"Motion Picture & Video": "Cinema e vídeo",
		"Music": "Música",
		"Newspaper Publishers": "Editoras de jornais",
		"Online Auctions": "Leilões online",
		"Pension Funds": "Fundos de pensão",
		"Pharmaceuticals": "Farmacêuticos",
		"Private Equity": "Capital privado",
		"Publishing": "Publicação",
		"Real Estate": "Imobiliário",
		"Retail & Wholesale": "Varejo e atacado",
		"Securities & Commodity Exchanges": "Bolsa de valores e mercadorias",
		"Service": "Serviço",
		"Soap & Detergent": "Sabões e detergentes",
		"Software": "Software",
		"Sports": "Esportes",
		"Technology": "Tecnologia",
		"Telecommunications": "Telecomunicações",
		"Television": "Televisão",
		"Transportation": "Transporte",
		"Venture Capital": "Capital de risco",
	},
	"Activity Type": {
		"Communication": "Comunicação",
		"Execution": "Execução",
		"Planning": "Planejamento",
		"Proposal Writing": "Elaboração de proposta",
		"Research": "Pesquisa",
	},
	"UOM": {
		"Box": "Caixa",
		"Centimeter": "Centímetro",
		"Day": "Dia",
		"Dozen": "Dúzia",
		"Foot": "Pé",
		"Gram": "Grama",
		"Hour": "Hora",
		"Inch": "Polegada",
		"Kilogram": "Quilograma",
		"Kilometer": "Quilômetro",
		"Liter": "Litro",
		"Meter": "Metro",
		"Minute": "Minuto",
		"Month": "Mês",
		"Nos": "Un",
		"Pair": "Par",
		"Second": "Segundo",
		"Set": "Conjunto",
		"Square Centimeter": "Centímetro quadrado",
		"Square Foot": "Pé quadrado",
		"Square Inch": "Polegada quadrada",
		"Square Meter": "Metro quadrado",
		"Unit": "Unidade",
		"Week": "Semana",
		"Year": "Ano",
	},
}

SYSTEM_SETTINGS_DEFAULTS = {
	"country": "Brazil",
	"language": "pt-BR",
	"time_zone": "America/Sao_Paulo",
	"currency": "BRL",
	"date_format": "dd/mm/yyyy",
	"time_format": "HH:mm:ss",
	"number_format": "#.###,##",
	"use_number_format_from_currency": 0,
	"first_day_of_the_week": "Sunday",
	"app_name": "SOL Provedor",
}

GLOBAL_DEFAULTS = {
	"country": "Brazil",
	"default_currency": "BRL",
}


ITEM_PORTUGUESE_LABELS = {
	"Item": {
		"details": "Detalhes",
		"stock_uom": "Unidade de medida padrão",
		"accounting": "Financeiro",
		"uom_tab": "Unidade de Medida",
		"tax_tab": "Fiscal",
		"inventory_section": "Estoque",
		"purchasing_tab": "Requisições",
		"sales_details": "Venda",
		"manufacturing": "Indústria",
		"quality_tab": "Qualidade",
		"pricing_tab": "Precificação",
		"dashboard_tab": "Relacionamentos",
		"item_defaults": "Configurações padrão do item",
		"deferred_accounting_section": "Contabilidade diferida",
		"enable_deferred_expense": "Ativar despesa diferida",
		"enable_deferred_revenue": "Ativar receita diferida",
		"no_of_months": "Quantidade de meses (receita)",
		"no_of_months_exp": "Quantidade de meses (despesa)",
		"opening_stock": "Estoque inicial",
		"valuation_rate": "Taxa de avaliação",
		"standard_rate": "Preço de venda padrão",
		"include_item_in_manufacturing": "Incluir item na fabricação",
		"asset_naming_series": "Série de numeração do ativo",
		"shelf_life_in_days": "Vida útil em dias",
		"end_of_life": "Fim da vida útil",
		"default_material_request_type": "Tipo padrão de requisição de material",
		"warranty_period": "Período de garantia (em dias)",
		"reorder_section": "Reposição automática",
		"reorder_levels": "Níveis de reposição por depósito",
		"serial_nos_and_batches": "Números de série / lotes",
		"has_batch_no": "Possui lote",
		"create_new_batch": "Criar novo lote automaticamente",
		"batch_number_series": "Série de numeração de lote",
		"has_expiry_date": "Possui data de validade",
		"retain_sample": "Reter amostra",
		"sample_quantity": "Quantidade máxima da amostra",
		"has_serial_no": "Possui número de série",
		"serial_no_series": "Série do número de série",
		"variants_section": "Variações",
		"variant_of": "Variação de",
		"has_variants": "Possui variações",
		"variant_based_on": "Variação baseada em",
		"attributes": "Características das variações",
		"purchase_uom": "Unidade de medida padrão para compra",
		"min_order_qty": "Quantidade mínima do pedido",
		"lead_time_days": "Prazo de entrega em dias",
		"supplier_details": "Dados dos fornecedores",
		"delivered_by_supplier": "Entregue pelo fornecedor (venda direta)",
		"supplier_items": "Itens dos fornecedores",
		"foreign_trade_details": "Dados de comércio exterior",
		"country_of_origin": "País de origem",
		"sales_uom": "Unidade de medida padrão para venda",
		"max_discount": "Desconto máximo (%)",
		"customer_details": "Dados dos clientes",
		"customer_items": "Itens dos clientes",
		"inspection_required_before_purchase": "Inspeção obrigatória antes da compra",
		"inspection_required_before_delivery": "Inspeção obrigatória antes da entrega",
		"default_bom": "Lista de materiais padrão",
		"is_sub_contracted_item": "Item subcontratado",
		"customer_code": "Código do cliente",
		"total_projected_qty": "Quantidade total projetada",
		"purchase_tax_withholding_category": "Categoria de retenção de imposto na compra",
		"sales_tax_withholding_category": "Categoria de retenção de imposto na venda",
		"production_capacity": "Capacidade de produção",
		"auto_create_assets": "Criar ativos automaticamente na compra",
		"default_item_manufacturer": "Fabricante padrão do item",
		"default_manufacturer_part_no": "Código de peça padrão do fabricante",
		"grant_commission": "Conceder comissão",
		"is_grouped_asset": "Criar ativo agrupado",
		"inventory_settings_section": "Configurações de estoque",
		"inventory_valuation_section": "Avaliação do estoque",
		"stock_levels_section": "Níveis de estoque",
		"uom_conversion_details_column": "Conversões de unidade de medida",
		"section_break_zlmj": "Características do item",
		"item_prices_column": "Preços do item",
		"company_restrictions_section": "Restrições por empresa",
		"restrict_to_companies": "Restringir às empresas",
		"allowed_companies": "Empresas permitidas",
	},
	"Item Default": {
		"company": "Empresa",
		"default_warehouse": "Depósito padrão",
		"default_price_list": "Lista de preços padrão",
		"default_discount_account": "Conta de descontos padrão",
		"default_inventory_account": "Conta de estoque padrão",
		"inventory_account_currency": "Moeda da conta de estoque",
		"column_break_general": "Padrão herdado",
		"vf_default_warehouse": "Depósito",
		"vf_default_price_list": "Lista de preços",
		"vf_default_discount_account": "Conta de descontos",
		"vf_default_inventory_account": "Conta de estoque",
		"purchase_defaults": "Configurações padrão de compra",
		"buying_cost_center": "Centro de custo de compras",
		"default_supplier": "Fornecedor padrão",
		"selling_cost_center": "Centro de custo de vendas",
		"expense_account": "Conta de despesas",
		"income_account": "Conta de receitas",
		"default_provisional_account": "Conta provisória (serviço)",
		"purchase_expense_account": "Conta de despesas de compra",
		"purchase_expense_contra_account": "Contrapartida das despesas de compra",
		"expenses_added_to_stock_account": "Conta de despesas adicionadas ao estoque",
		"expenses_added_to_stock_contra_account": "Contrapartida das despesas adicionadas ao estoque",
		"purchase_price_variance_account": "Conta de variação do preço de compra",
		"manufacturing_variance_account": "Conta de variação da fabricação",
		"vf_buying_cost_center": "Centro de custo de compras",
		"vf_default_supplier": "Fornecedor",
		"vf_expense_account": "Conta de despesas",
		"vf_default_provisional_account": "Conta provisória (serviço)",
		"vf_purchase_expense_account": "Conta de despesas de compra",
		"vf_purchase_expense_contra_account": "Contrapartida das despesas de compra",
		"vf_expenses_added_to_stock_account": "Despesas adicionadas ao estoque",
		"vf_expenses_added_to_stock_contra_account": "Contrapartida das despesas de estoque",
		"selling_defaults": "Configurações padrão de venda",
		"vf_selling_cost_center": "Centro de custo de vendas",
		"vf_income_account": "Conta de receitas",
		"cost_of_good_sold_section": "Custo dos produtos vendidos",
		"default_cogs_account": "Conta de custo dos produtos vendidos",
		"vf_default_cogs_account": "Conta de custo dos produtos vendidos",
		"deferred_accounting_defaults_section": "Configurações padrão da contabilidade diferida",
		"deferred_expense_account": "Conta de despesas diferidas",
		"deferred_revenue_account": "Conta de receitas diferidas",
		"vf_deferred_expense_account": "Conta de despesas diferidas",
		"vf_deferred_revenue_account": "Conta de receitas diferidas",
		"column_break_njfg": "Substituição específica do item",
	},
	"Item Reorder": {
		"warehouse_group": "Verificar disponibilidade no depósito",
		"warehouse": "Depósito",
		"warehouse_reorder_level": "Nível de reposição",
		"warehouse_reorder_qty": "Quantidade para reposição",
		"material_request_type": "Tipo de requisição de material",
	},
	"UOM Conversion Detail": {
		"uom": "Unidade de medida",
		"conversion_factor": "Fator de conversão",
	},
	"Item Variant Attribute": {
		"variant_of": "Variação de",
		"attribute": "Característica",
		"attribute_value": "Valor da característica",
		"numeric_values": "Valores numéricos",
		"from_range": "Faixa inicial",
		"to_range": "Faixa final",
		"increment": "Incremento",
		"disabled": "Desativado",
	},
	"Item Supplier": {
		"supplier": "Fornecedor",
		"supplier_part_no": "Código do fornecedor",
	},
	"Item Customer Detail": {
		"customer_name": "Cliente",
		"customer_group": "Grupo de clientes",
		"ref_code": "Código de referência",
	},
	"Item Barcode": {"barcode": "Código de barras", "barcode_type": "Tipo de código de barras"},
	"Item Tax": {"item_tax_template": "Modelo de imposto do item", "tax_category": "Categoria fiscal", "valid_from": "Válido a partir de", "maximum_net_rate": "Valor líquido máximo", "minimum_net_rate": "Valor líquido mínimo"},
	"Company Restriction": {"company": "Empresa"},
}


ITEM_PORTUGUESE_DESCRIPTIONS = {
	"variant_of": "Se o item for uma variação de outro, descrição, imagem, preços e impostos serão herdados do modelo, salvo quando informados explicitamente.",
	"disabled": "Itens desativados não podem ser selecionados em transações.",
	"enable_deferred_expense": "A despesa deste item será reconhecida ao longo de vários meses, como em seguros ou licenças anuais pagos antecipadamente.",
	"enable_deferred_revenue": "A receita deste item será reconhecida ao longo de vários meses, em vez de integralmente, como em uma assinatura anual paga antecipadamente.",
	"is_stock_item": "O sistema fará um lançamento no razão de estoque para cada movimentação deste item. Desmarque para serviços ou itens sem controle de estoque.",
	"is_fixed_asset": "Marque se este item for um ativo da empresa, como máquinas, equipamentos ou móveis.",
	"allow_alternative_item": "Permite substituir este item por outro da lista de itens alternativos quando não houver estoque.",
	"include_item_in_manufacturing": "Marque para matérias-primas utilizadas na fabricação. Desmarque para serviços adicionais.",
	"standard_rate": "Cria automaticamente um preço para o item ao salvá-lo.",
	"end_of_life": "Define a data após a qual o item não poderá mais ser usado em transações ou fabricação.",
	"reorder_levels": "Também se aplica às variações, salvo quando substituído nelas.",
	"has_batch_no": "Controla este item por lotes. Não pode ser alterado depois que houver movimentação de estoque.",
	"create_new_batch": "O número do lote será criado automaticamente quando não for informado na movimentação. Desmarque para sempre digitá-lo manualmente.",
	"batch_number_series": "Define a série usada para gerar automaticamente os números dos lotes.",
	"has_expiry_date": "O lote será controlado por data de validade, informada no cadastro do lote.",
	"retain_sample": "Reserva uma pequena amostra de cada lote para análises futuras.",
	"sample_quantity": "Quantidade máxima da amostra que poderá ser retida.",
	"has_serial_no": "Controla cada unidade com um número de série exclusivo para garantia e devoluções.",
	"serial_no_series": "Define a série usada para gerar automaticamente os números de série.",
	"has_variants": "Quando possui variações, este item funciona como modelo e não é selecionado diretamente nas transações.",
	"is_purchase_item": "Permite utilizar este item em transações de compra.",
	"min_order_qty": "A quantidade mínima deve usar a unidade de medida padrão do estoque.",
	"safety_stock": "Nível mínimo mantido como margem de segurança e utilizado no cálculo da reposição recomendada.",
	"lead_time_days": "Tempo médio necessário para o fornecedor realizar a entrega.",
	"last_purchase_rate": "Valor da última compra do item, atualizado automaticamente pelo sistema.",
	"is_sales_item": "Permite utilizar este item em transações de venda.",
	"max_discount": "Percentual máximo de desconto permitido na venda deste item.",
	"is_customer_provided_item": "Marque quando o item for fornecido pelo cliente e recebido por uma movimentação de estoque.",
	"delivered_by_supplier": "Trata o item como entregue diretamente pelo fornecedor por padrão nas vendas e compras.",
	"inspection_required_before_purchase": "Exige uma inspeção de qualidade antes de gerar o recebimento da compra.",
	"inspection_required_before_delivery": "Exige uma inspeção de qualidade antes de gerar a nota de entrega.",
	"is_sub_contracted_item": "Marque quando um fornecedor fabricar este item para sua empresa.",
	"taxes": "Também se aplica às variações do item.",
	"over_delivery_receipt_allowance": "Percentual excedente permitido na entrega ou no recebimento em relação ao pedido.",
	"over_billing_allowance": "Percentual de faturamento excedente permitido em relação ao pedido.",
	"grant_commission": "Inclui as vendas deste item nos cálculos de comissão dos vendedores e parceiros.",
	"is_grouped_asset": "Cria um único ativo agrupado quando várias unidades forem compradas juntas.",
	"allow_negative_stock": "Permite que o saldo deste item fique abaixo de zero, mesmo quando o estoque negativo estiver desativado globalmente.",
	"restrict_to_companies": "Quando marcado, o item estará disponível somente para as empresas listadas abaixo.",
}


ITEM_DEFAULT_PORTUGUESE_DESCRIPTIONS = {
	"default_price_list": "Lista de preços padrão utilizada na compra ou venda deste item.",
	"default_inventory_account": "Conta na qual o valor do estoque deste item será controlado.",
	"buying_cost_center": "Centro de custo usado para controlar as despesas de compra deste item.",
	"default_supplier": "Fornecedor selecionado automaticamente nas novas compras.",
	"expense_account": "Conta debitada com o custo deste item na compra.",
	"default_provisional_account": "Conta provisória usada para serviços antes do recebimento da fatura.",
	"purchase_expense_account": "Conta usada para despesas adicionais da compra, como frete e tributos.",
	"purchase_expense_contra_account": "Conta de contrapartida das despesas adicionais da compra.",
	"expenses_added_to_stock_account": "Conta que controla valores adicionados ao estoque por movimentações e conciliações.",
	"expenses_added_to_stock_contra_account": "Conta de contrapartida das despesas adicionadas ao estoque.",
	"purchase_price_variance_account": "Conta que registra a diferença entre o preço de compra e o custo padrão.",
	"manufacturing_variance_account": "Conta que registra a diferença entre o custo de fabricação e o custo padrão.",
	"selling_cost_center": "Centro de custo usado para controlar a receita das vendas deste item.",
	"income_account": "Conta creditada com a receita da venda deste item.",
	"default_cogs_account": "Conta que recebe o custo dos produtos vendidos.",
}


def setup_item_portuguese_fields():
	for doctype, fields in ITEM_PORTUGUESE_LABELS.items():
		if not frappe.db.exists("DocType", doctype):
			continue
		meta = frappe.get_meta(doctype)
		for fieldname, label in fields.items():
			if meta.has_field(fieldname):
				make_property_setter(doctype, fieldname, "label", label, "Data")

	for fieldname, description in ITEM_PORTUGUESE_DESCRIPTIONS.items():
		if frappe.get_meta("Item").has_field(fieldname):
			make_property_setter("Item", fieldname, "description", description, "Text")

	for fieldname, description in ITEM_DEFAULT_PORTUGUESE_DESCRIPTIONS.items():
		if frappe.get_meta("Item Default").has_field(fieldname):
			make_property_setter("Item Default", fieldname, "description", description, "Text")

	if frappe.get_meta("Item Customer Detail").has_field("ref_code"):
		make_property_setter(
			"Item Customer Detail",
			"ref_code",
			"description",
			"Informe o código usado pelo cliente para este item. Ele aparecerá nos pedidos de venda como referência.",
			"Text",
		)

	make_property_setter("Item", "brand", "label", "Fabricante", "Data")
	make_property_setter("Item", "brand", "allow_in_quick_entry", 1, "Check")
	make_property_setter(
		"Item",
		"brand",
		"mandatory_depends_on",
		"eval:doc.is_stock_item || doc.is_fixed_asset",
		"Code",
	)
	make_property_setter("Item", "is_stock_item", "read_only_depends_on", "", "Code")
	make_property_setter("Item", "is_fixed_asset", "read_only_depends_on", "", "Code")

	frappe.clear_cache(doctype="Item")


def setup_service_subjects():
	for title, description in DEFAULT_SERVICE_SUBJECTS:
		if frappe.db.exists("Assunto de Atendimento", title):
			continue
		frappe.get_doc({
			"doctype": "Assunto de Atendimento",
			"assunto": title,
			"descricao": description,
			"ativo": 1,
		}).insert(ignore_permissions=True)


def setup_provider_services():
	for title, description in DEFAULT_PROVIDER_SERVICES:
		if frappe.db.exists("Servico do Provedor", title):
			continue
		frappe.get_doc({
			"doctype": "Servico do Provedor",
			"servico": title,
			"descricao": description,
			"ativo": 1,
		}).insert(ignore_permissions=True)


def setup_customer_fields():
	migrate_customer_olt_link()
	create_custom_fields(CUSTOM_FIELDS, update=True)
	from sol_brasil.central_cobranca import backfill_invoice_reference_months

	backfill_invoice_reference_months(ignore_permissions=True)
	setup_customer_numeric_naming()
	backfill_customer_numeric_codes()
	remove_obsolete_radius_fields()
	hide_legacy_customer_access_fields()
	backfill_customer_contract_links()
	backfill_subscription_internet_plans()
	migrate_customer_access_to_subscriptions()
	reorder_subscription_tabs()
	setup_service_subjects()
	setup_provider_services()
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
	make_property_setter("Address", "email_id", "hidden", 1, "Check")
	make_property_setter("Address", "phone", "hidden", 1, "Check")
	make_property_setter("Address", "fax", "hidden", 1, "Check")
	make_property_setter("Maintenance Visit Purpose", "item_code", "hidden", 1, "Check")
	make_property_setter("Maintenance Visit Purpose", "item_name", "hidden", 1, "Check")
	make_property_setter("Maintenance Visit Purpose", "service_person", "label", "Técnico responsável", "Data")
	make_property_setter("Maintenance Visit Purpose", "service_person", "reqd", 0, "Check")
	make_property_setter("Maintenance Visit Purpose", "description", "label", "Descrição / orientação", "Data")
	make_property_setter("Maintenance Visit Purpose", "description", "reqd", 0, "Check")
	make_property_setter("Maintenance Visit Purpose", "work_done", "label", "Descrição", "Data")
	make_property_setter("Maintenance Visit Purpose", "work_done", "reqd", 0, "Check")
	if frappe.get_meta("Address").has_field("tax_category"):
		make_property_setter("Address", "tax_category", "hidden", 1, "Check")
	backfill_customer_contract_links()
	reorder_customer_relationships_tab()


def migrate_customer_olt_link():
	field_name = frappe.db.get_value(
		"Custom Field", {"dt": "Customer", "fieldname": "custom_olt"}, "name"
	)
	if not field_name:
		return
	fieldtype = frappe.db.get_value("Custom Field", field_name, "fieldtype")
	if fieldtype == "Data":
		# Data e Link usam a mesma coluna textual. Alterar somente os metadados
		# preserva os valores existentes e permite que o Frappe valide o vínculo.
		frappe.db.set_value(
			"Custom Field",
			field_name,
			{"fieldtype": "Link", "options": "OLT"},
			update_modified=False,
		)
		frappe.clear_cache(doctype="Customer")


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


def setup_customer_numeric_naming():
	"""Name new customers with numeric-only sequential IDs such as 000001."""
	frappe.defaults.set_global_default("cust_master_name", "Naming Series")
	make_property_setter("Customer", "naming_series", "options", "0", "Text")
	make_property_setter("Customer", "naming_series", "default", "0", "Text")
	make_property_setter("Customer", "naming_series", "hidden", 1, "Check")
	make_property_setter("Customer", "naming_series", "reqd", 0, "Check")
	frappe.clear_cache(doctype="Customer")


def backfill_customer_numeric_codes():
	"""Give legacy customers a numeric code and continue new IDs after that range."""
	existing_codes = [
		int(code)
		for code in frappe.get_all(
			"Customer", filters={"custom_customer_code": ["is", "set"]}, pluck="custom_customer_code"
		)
		if str(code).isdigit()
	]
	next_code = max(existing_codes, default=0)
	for customer in frappe.get_all(
		"Customer",
		filters={"custom_customer_code": ["is", "not set"]},
		pluck="name",
		order_by="creation asc",
	):
		next_code += 1
		frappe.db.set_value(
			"Customer", customer, "custom_customer_code", f"{next_code:06d}", update_modified=False
		)

	frappe.db.sql(
		"""
		INSERT INTO `tabSeries` (`name`, `current`)
		VALUES (%s, %s)
		ON DUPLICATE KEY UPDATE `current` = GREATEST(`current`, VALUES(`current`))
		""",
		("0", next_code),
	)


def remove_obsolete_radius_fields():
	for fieldname in (
		"custom_radius_profile",
		"custom_pppoe_accesses_section",
		"custom_pppoe_accesses_panel",
	):
		name = frappe.db.get_value(
			"Custom Field", {"dt": "Customer", "fieldname": fieldname}, "name"
		)
		if name:
			frappe.delete_doc("Custom Field", name, ignore_permissions=True, force=True)
	frappe.clear_cache(doctype="Customer")


LEGACY_CUSTOMER_ACCESS_FIELDS = (
	"custom_provider_access_section", "custom_pppoe_username", "custom_pppoe_password",
	"custom_linked_subscription", "custom_change_contract", "custom_provider_access_column",
	"custom_connection_status", "custom_subscription_plan", "custom_activation_date",
	"custom_provider_network_section", "custom_ipv4_address", "custom_mac_address",
	"custom_vlan_id", "custom_optical_splitter", "custom_installation_box",
	"custom_provider_network_column", "custom_olt", "custom_olt_slot", "custom_pon",
	"custom_pon_port", "custom_onu_serial", "custom_onu_id", "custom_onu_id_type",
	"custom_onu_auth_type", "custom_onu_auth_password", "custom_onu_number",
	"custom_onu_model", "custom_onu_rx_signal", "custom_onu_tx_signal",
	"custom_onu_signal_status", "custom_onu_signal_checked_at", "custom_network_notes",
)


def hide_legacy_customer_access_fields():
	for fieldname in LEGACY_CUSTOMER_ACCESS_FIELDS:
		name = frappe.db.get_value("Custom Field", {"dt": "Customer", "fieldname": fieldname}, "name")
		if name:
			frappe.db.set_value("Custom Field", name, "hidden", 1, update_modified=False)
	frappe.clear_cache(doctype="Customer")


def migrate_customer_access_to_subscriptions():
	if not frappe.db.table_exists("Subscription") or not frappe.get_meta("Subscription").has_field("custom_pppoe_username"):
		return
	fields = [field for field in LEGACY_CUSTOMER_ACCESS_FIELDS if field not in {
		"custom_provider_access_section", "custom_linked_subscription", "custom_change_contract",
		"custom_provider_access_column", "custom_subscription_plan", "custom_provider_network_section",
		"custom_provider_network_column",
	}]
	for customer_name in frappe.get_all("Customer", filters={"custom_linked_subscription": ["is", "set"]}, pluck="name"):
		customer = frappe.get_doc("Customer", customer_name)
		if not frappe.db.exists("Subscription", customer.custom_linked_subscription):
			continue
		contract = frappe.get_doc("Subscription", customer.custom_linked_subscription)
		changed = False
		for fieldname in fields:
			if not contract.meta.has_field(fieldname):
				continue
			value = customer.get(fieldname)
			if customer.meta.get_field(fieldname).fieldtype == "Password" and value:
				value = customer.get_password(fieldname, raise_exception=False)
			target_has_value = contract.get(fieldname) not in (None, "")
			if fieldname == "custom_connection_status" and contract.get(fieldname) == "Aguardando instalação":
				target_has_value = False
			if target_has_value:
				continue
			if value not in (None, ""):
				contract.set(fieldname, value)
				changed = True
		if changed:
			contract.flags.ignore_validate_update_after_submit = True
			contract.flags.in_access_migration = True
			contract.flags.ignore_links = True
			contract.save(ignore_permissions=True)


def backfill_subscription_internet_plans():
	for row in frappe.get_all("Subscription Plan Detail", fields=["parent", "plan"], order_by="parent, idx asc"):
		if not row.parent or not row.plan:
			continue
		if not frappe.db.get_value("Subscription", row.parent, "custom_internet_plan"):
			frappe.db.set_value(
				"Subscription", row.parent, "custom_internet_plan", row.plan, update_modified=False
			)


def reorder_subscription_tabs():
	"""Make Provedor the primary Subscription tab and Detalhes the second tab."""
	frappe.clear_cache(doctype="Subscription")
	fieldnames = [field.fieldname for field in frappe.get_meta("Subscription").fields]
	provider_fields = [
		"custom_provider_tab", "custom_access_section", "custom_internet_plan",
		"custom_pppoe_username", "custom_pppoe_password", "custom_access_column",
		"custom_connection_status", "custom_activation_date", "custom_bandwidth_reduced",
		"custom_effective_download_mbps", "custom_effective_upload_mbps",
		"custom_effective_rate_limit", "custom_radius_provisioning_state",
		"custom_radius_provisioning_version", "custom_radius_last_sync",
		"custom_radius_last_error", "custom_radius_snapshot_hash", "custom_network_section",
		"custom_ipv4_address", "custom_mac_address", "custom_vlan_id",
		"custom_optical_splitter", "custom_installation_box", "custom_network_column",
		"custom_olt", "custom_olt_slot", "custom_olt_slot_select", "custom_pon",
		"custom_pon_select", "custom_installation_box_link", "custom_cto_port", "custom_pon_port",
		"custom_onu_serial", "custom_onu_id", "custom_onu_id_type",
		"custom_onu_auth_type", "custom_onu_auth_password", "custom_onu_number",
		"custom_onu_model", "custom_onu_rx_signal", "custom_onu_tx_signal",
		"custom_onu_signal_status", "custom_onu_signal_checked_at", "custom_network_notes",
	]
	provider_fields = [field for field in provider_fields if field in fieldnames]
	details_tab = ["custom_details_tab"] if "custom_details_tab" in fieldnames else []
	remaining = [field for field in fieldnames if field not in provider_fields and field not in details_tab]
	make_property_setter(
		"Subscription",
		None,
		"field_order",
		json.dumps(provider_fields + details_tab + remaining),
		"Text",
	)
	frappe.clear_cache(doctype="Subscription")


def setup_fiberhome_roles():
	for role_name in (
		"Consulta de Rede FiberHome",
		"Operação de Rede FiberHome",
		"Administração FiberHome",
	):
		if not frappe.db.exists("Role", role_name):
			frappe.get_doc({"doctype": "Role", "role_name": role_name}).insert(ignore_permissions=True)


def setup_portuguese_brazil_defaults():
	frappe.db.set_default("lang", "pt-BR")
	system_settings = frappe.get_meta("System Settings")
	for fieldname, value in SYSTEM_SETTINGS_DEFAULTS.items():
		if system_settings.has_field(fieldname):
			frappe.db.set_value("System Settings", "System Settings", fieldname, value)
	global_defaults = frappe.get_meta("Global Defaults")
	for fieldname, value in GLOBAL_DEFAULTS.items():
		if global_defaults.has_field(fieldname):
			frappe.db.set_value("Global Defaults", "Global Defaults", fieldname, value)
	if frappe.db.exists("User", "Administrator"):
		frappe.db.set_value("User", "Administrator", "language", "pt-BR")


def setup_portuguese_brazil_master_data():
	for doctype, renames in STANDARD_MASTER_RENAMES.items():
		if not frappe.db.table_exists(doctype):
			continue
		for old_name, new_name in renames.items():
			if old_name == new_name:
				continue
			if not frappe.db.exists(doctype, old_name):
				continue
			frappe.rename_doc(
				doctype,
				old_name,
				new_name,
				force=True,
				merge=frappe.db.exists(doctype, new_name),
				show_alert=False,
				rebuild_search=False,
			)


def after_install():
	setup_portuguese_brazil_defaults()
	setup_portuguese_brazil_master_data()
	setup_customer_fields()
	setup_item_portuguese_fields()
	setup_fiberhome_roles()
	from sol_brasil.workspace import sync_provider_workspaces

	sync_provider_workspaces()


def after_migrate():
	setup_portuguese_brazil_defaults()
	setup_portuguese_brazil_master_data()
	setup_customer_fields()
	setup_item_portuguese_fields()
	setup_fiberhome_roles()
	from sol_brasil.workspace import sync_provider_workspaces

	sync_provider_workspaces()
