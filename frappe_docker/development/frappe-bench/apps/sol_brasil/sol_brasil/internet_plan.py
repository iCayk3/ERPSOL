import json

import frappe
from frappe import _
from frappe.utils import cint


def validate_internet_plan(doc, method=None):
	for fieldname, label in (
		("custom_download_mbps", _("Download")),
		("custom_upload_mbps", _("Upload")),
	):
		if cint(doc.get(fieldname)) < 0:
			frappe.throw(_("{0} não pode ser menor que zero.").format(label))

	if cint(doc.get("custom_session_limit")) < 1:
		frappe.throw(_("O limite de sessões simultâneas deve ser pelo menos 1."))
	if cint(doc.get("custom_accounting_interval")) < 60:
		frappe.throw(_("O intervalo de accounting deve ser de pelo menos 60 segundos."))

	upload = cint(doc.get("custom_upload_mbps"))
	download = cint(doc.get("custom_download_mbps"))
	doc.custom_mikrotik_rate_limit = f"{upload}M/{download}M" if upload or download else None

	if not doc.get("custom_radius_attributes"):
		return
	try:
		attributes = json.loads(doc.custom_radius_attributes)
	except (TypeError, ValueError):
		frappe.throw(_("Atributos RADIUS adicionais deve conter um objeto JSON válido."))
	if not isinstance(attributes, dict):
		frappe.throw(_("Atributos RADIUS adicionais deve ser um objeto JSON."))
	for key in attributes:
		if any(secret in key.lower() for secret in ("password", "senha", "secret")):
			frappe.throw(_("Não inclua senhas ou segredos nos atributos RADIUS adicionais."))
	doc.custom_radius_attributes = json.dumps(attributes, ensure_ascii=False, sort_keys=True, indent=2)
