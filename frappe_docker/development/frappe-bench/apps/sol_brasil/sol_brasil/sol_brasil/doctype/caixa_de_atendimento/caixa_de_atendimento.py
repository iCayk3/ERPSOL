import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import cint


class CaixadeAtendimento(Document):
	def validate(self):
		if cint(self.capacidade) < 0:
			frappe.throw(_("A quantidade de portas não pode ser negativa."))

		capacity = frappe.db.get_value(
			"OLT", self.olt, ["quantidade_slots_pon", "pons_por_slot"], as_dict=True
		)
		if not capacity:
			frappe.throw(_("Selecione uma OLT válida."))

		slot = cint(self.slot)
		pon = cint(self.pon)
		if slot < 1 or slot > cint(capacity.quantidade_slots_pon):
			frappe.throw(
				_("O slot deve estar entre 1 e {0} para a OLT selecionada.").format(
					capacity.quantidade_slots_pon
				)
			)
		if pon < 1 or pon > cint(capacity.pons_por_slot):
			frappe.throw(
				_("A PON deve estar entre 1 e {0} para a OLT selecionada.").format(
					capacity.pons_por_slot
				)
			)
