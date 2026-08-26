import frappe
from frappe import _
from frappe.utils import cint


@frappe.whitelist()
def get_olt_ctos(olt):
	frappe.has_permission("OLT", "read", olt, throw=True)
	rows = frappe.get_all(
		"Caixa de Atendimento",
		filters={"olt": olt},
		fields=["name", "identificacao", "situacao", "slot", "pon", "capacidade", "endereco_referencia"],
		order_by="slot asc, pon asc, identificacao asc",
	)
	for row in rows:
		row.occupied = frappe.db.count(
			"Subscription",
			filters={
				"custom_installation_box_link": row.name,
				"custom_pppoe_username": ["is", "set"],
				"custom_connection_status": ["!=", "Cancelado"],
				"custom_cto_port": ["is", "set"],
			},
		)
		row.available = max(cint(row.capacidade) - row.occupied, 0)
	return rows


@frappe.whitelist()
def get_cto_occupants(cto):
	frappe.has_permission("Caixa de Atendimento", "read", cto, throw=True)
	return frappe.get_all(
		"Subscription",
		filters={
			"custom_installation_box_link": cto,
			"custom_pppoe_username": ["is", "set"],
			"custom_connection_status": ["!=", "Cancelado"],
		},
		fields=[
			"name", "party", "custom_cto_port", "custom_pppoe_username",
			"custom_connection_status", "custom_installation_address",
		],
		order_by="custom_cto_port asc",
	)
