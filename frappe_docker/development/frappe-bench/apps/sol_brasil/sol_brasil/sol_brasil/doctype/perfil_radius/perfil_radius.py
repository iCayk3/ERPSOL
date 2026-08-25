import json
import re

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import cint


class PerfilRADIUS(Document):
	def validate(self):
		self.codigo = re.sub(r"[^a-z0-9_-]+", "-", (self.codigo or "").strip().lower()).strip("-")
		if not self.codigo:
			frappe.throw(_("Informe um código técnico válido para o perfil."))
		for fieldname, label in (
			("download_mbps", _("Download")),
			("upload_mbps", _("Upload")),
		):
			if cint(self.get(fieldname)) < 0:
				frappe.throw(_("{0} não pode ser menor que zero.").format(label))
		if cint(self.limite_sessoes) < 1:
			frappe.throw(_("O limite de sessões deve ser pelo menos 1."))
		if cint(self.acct_interim_interval) < 60:
			frappe.throw(_("O intervalo de accounting deve ser de pelo menos 60 segundos."))
		self.mikrotik_rate_limit = f"{cint(self.upload_mbps)}M/{cint(self.download_mbps)}M"
		self._validate_additional_attributes()

	def _validate_additional_attributes(self):
		if not self.atributos_adicionais:
			return
		try:
			attributes = json.loads(self.atributos_adicionais)
		except (TypeError, ValueError):
			frappe.throw(_("Atributos adicionais deve conter um objeto JSON válido."))
		if not isinstance(attributes, dict):
			frappe.throw(_("Atributos adicionais deve ser um objeto JSON."))
		for key in attributes:
			if any(secret in key.lower() for secret in ("password", "senha", "secret")):
				frappe.throw(_("Não inclua senhas ou segredos nos atributos adicionais."))
		self.atributos_adicionais = json.dumps(attributes, ensure_ascii=False, sort_keys=True, indent=2)

	def on_update(self):
		previous = self.get_doc_before_save()
		if not previous:
			return
		tracked = {
			"plano", "tipo_perfil", "ativo", "download_mbps", "upload_mbps",
			"limite_sessoes", "acct_interim_interval", "pool_ipv4", "pool_ipv6",
			"filter_id", "atributos_adicionais",
		}
		if not any(previous.get(field) != self.get(field) for field in tracked):
			return
		from sol_brasil.radius_provisioning import queue_profile_update

		for access in frappe.get_all("Acesso PPPoE", filters={"perfil_radius": self.name}, pluck="name"):
			queue_profile_update(access)
