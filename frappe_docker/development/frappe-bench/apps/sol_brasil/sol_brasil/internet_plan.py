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
	if doc.get("custom_enable_overdue_reduction"):
		reduce_days = cint(doc.get("custom_reduce_after_days"))
		if reduce_days < 1:
			frappe.throw(_("A redução de banda deve ocorrer após pelo menos um dia de atraso."))
		block_days = cint(frappe.get_single("Regras de Negocio").block_after_days or 5)
		if reduce_days > block_days:
			frappe.throw(_("O dia da redução não pode ser posterior ao dia do bloqueio."))
		for fieldname, label in (
			("custom_download_reduction_percent", _("redução do download")),
			("custom_upload_reduction_percent", _("redução do upload")),
		):
			value = float(doc.get(fieldname) or 0)
			if value <= 0 or value >= 100:
				frappe.throw(_("A {0} deve ser maior que 0% e menor que 100%.").format(label))

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
