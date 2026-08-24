from ipaddress import ip_address

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import cint


class OLT(Document):
	def validate(self):
		self._validate_pon_capacity()
		self._validate_equipment_model()
		self._validate_management_ip()

	def _validate_pon_capacity(self):
		for fieldname, label in (
			("quantidade_slots_pon", _("Quantidade de slots PON")),
			("pons_por_slot", _("Portas PON por slot")),
		):
			value = cint(self.get(fieldname))
			if value < 0:
				frappe.throw(_("{0} não pode ser menor que zero.").format(label))

	def _validate_equipment_model(self):
		if not self.modelo:
			return

		item_brand = frappe.db.get_value("Item", self.modelo, "brand")
		if not item_brand:
			frappe.throw(_("O modelo selecionado precisa possuir uma fabricante no cadastro do item."))

		if not self.fabricante:
			self.fabricante = item_brand
		elif self.fabricante != item_brand:
			frappe.throw(_("O modelo selecionado não pertence à fabricante {0}.").format(self.fabricante))

	def _validate_management_ip(self):
		if not self.ip_gerenciamento:
			return

		try:
			self.ip_gerenciamento = str(ip_address(self.ip_gerenciamento.strip()))
		except ValueError:
			frappe.throw(_("Informe um endereço IP de gerenciamento válido."))
