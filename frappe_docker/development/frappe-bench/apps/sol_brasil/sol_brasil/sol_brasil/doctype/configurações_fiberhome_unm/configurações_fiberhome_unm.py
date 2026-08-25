from ipaddress import ip_address

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import cint


class ConfiguraçõesFiberHomeUNM(Document):
	def validate(self):
		self.host = (self.host or "").strip()
		if self.enabled and not self.host:
			frappe.throw(_("Informe o endereço do UNM."))
		try:
			if self.host:
				ip_address(self.host)
		except ValueError:
			frappe.throw(_("O host do UNM deve ser um endereço IPv4 ou IPv6 válido."))
		if not 1 <= cint(self.port) <= 65535:
			frappe.throw(_("Informe uma porta TL1 válida."))
		if not 2 <= cint(self.timeout_seconds) <= 30:
			frappe.throw(_("O timeout deve estar entre 2 e 30 segundos."))
