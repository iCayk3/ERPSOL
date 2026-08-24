import frappe
from frappe import _


def validate_item_manufacturer(doc, method=None):
	if (doc.is_stock_item or doc.is_fixed_asset) and not doc.brand:
		frappe.throw(_("Informe a fabricante para itens de estoque ou ativos imobilizados."))
