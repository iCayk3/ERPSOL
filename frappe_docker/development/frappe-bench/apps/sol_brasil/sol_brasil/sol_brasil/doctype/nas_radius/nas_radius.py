from ipaddress import ip_address, ip_network

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import cint


class NASRADIUS(Document):
	def validate(self):
		try:
			self.endereco_ip = str(ip_address((self.endereco_ip or "").strip()))
		except ValueError:
			frappe.throw(_("Informe um endereço IP válido para o NAS."))

		if self.rede_confiavel:
			try:
				self.rede_confiavel = str(ip_network(self.rede_confiavel.strip(), strict=False))
			except ValueError:
				frappe.throw(_("Informe uma rede confiável válida em notação CIDR."))

		if self.suporta_coa and not 1 <= cint(self.porta_coa) <= 65535:
			frappe.throw(_("A porta CoA/Disconnect deve estar entre 1 e 65535."))
