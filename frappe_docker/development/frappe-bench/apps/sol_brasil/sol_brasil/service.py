import frappe
from frappe import _
from frappe.utils import get_link_to_form
from frappe.utils.data import strip_html


def _subject_title(subject_name):
	return frappe.db.get_value("Assunto de Atendimento", subject_name, "assunto") if subject_name else None


def _add_customer_activity(customer, text):
	if customer and frappe.db.exists("Customer", customer):
		frappe.get_doc("Customer", customer).add_comment("Comment", text=text)


def validate_issue_subject(doc, method=None):
	if doc.status in ("Resolved", "Closed"):
		validate_issue_service_orders_completed(doc)
		answer = strip_html(doc.resolution_details or "").strip()
		if not answer:
			frappe.throw(
				_("Informe a resposta ou conclusão do atendimento antes de marcá-lo como resolvido ou fechado. A resposta pode indicar que o problema não foi solucionado."),
				title=_("Resposta obrigatória"),
			)
	if not doc.customer:
		return
	if not doc.custom_service_subject:
		frappe.throw(_("Selecione o assunto do atendimento."), title=_("Assunto obrigatório"))
	title = _subject_title(doc.custom_service_subject)
	if not title:
		frappe.throw(_("O assunto de atendimento selecionado não existe."))
	if not doc.subject:
		doc.subject = title


def validate_issue_service_orders_completed(doc):
	if doc.is_new():
		return

	service_orders = frappe.get_all(
		"Maintenance Visit",
		filters={"custom_origin_issue": doc.name, "docstatus": ["<", 2]},
		fields=["name", "docstatus", "completion_status"],
		order_by="creation asc",
	)
	pending = [
		row.name
		for row in service_orders
		if row.docstatus != 1 or row.completion_status != "Fully Completed"
	]
	if pending:
		frappe.throw(
			_("Conclua todas as ordens de serviço antes de fechar o atendimento. OS pendentes: {0}.").format(
				", ".join(frappe.bold(name) for name in pending)
			),
			title=_("Ordens de serviço pendentes"),
		)


def register_issue_creation(doc, method=None):
	if not doc.customer:
		return
	_add_customer_activity(
		doc.customer,
		_("Atendimento {0} criado com o assunto {1}.").format(
			get_link_to_form("Issue", doc.name, doc.name), frappe.bold(_subject_title(doc.custom_service_subject))
		),
	)


def register_issue_update(doc, method=None):
	previous = doc.get_doc_before_save()
	if not previous or not doc.customer:
		return
	status_changed = previous.status != doc.status
	answer_changed = previous.resolution_details != doc.resolution_details
	if doc.status not in ("Resolved", "Closed") or not (status_changed or answer_changed):
		return
	status_label = "Resolvido" if doc.status == "Resolved" else "Fechado"
	answer = strip_html(doc.resolution_details or "").strip()
	_add_customer_activity(
		doc.customer,
		_("Atendimento {0} marcado como {1}. Resposta/conclusão: {2}").format(
			get_link_to_form("Issue", doc.name, doc.name),
			frappe.bold(status_label),
			answer,
		),
	)


def validate_service_order_links(doc, method=None):
	if not doc.custom_service_subject:
		frappe.throw(_("Selecione o assunto do atendimento."), title=_("Assunto obrigatório"))
	if doc.custom_origin_issue:
		issue_customer = frappe.db.get_value("Issue", doc.custom_origin_issue, "customer")
		if not issue_customer or issue_customer != doc.customer:
			frappe.throw(_("O atendimento de origem não pertence ao cliente da ordem de serviço."))
	for row in doc.get("purposes") or []:
		if not row.custom_provider_service:
			frappe.throw(_("Selecione o serviço a executar em todas as linhas da ordem de serviço."))


def validate_service_order_completion(doc, method=None):
	if doc.completion_status != "Fully Completed":
		frappe.throw(
			_("Uma ordem de serviço parcialmente concluída deve permanecer em rascunho. Use Salvar para continuar depois; selecione Totalmente concluído somente quando for enviar e fechar a OS."),
			title=_("OS ainda em execução"),
		)

	missing = [row.idx for row in (doc.get("purposes") or []) if not strip_html(row.work_done or "").strip()]
	if missing:
		frappe.throw(
			_("Informe a descrição do que foi realizado antes de concluir a ordem de serviço. Linhas pendentes: {0}.").format(
				", ".join(str(index) for index in missing)
			),
			title=_("Descrição obrigatória na conclusão"),
		)


def create_or_link_issue_for_service_order(doc, method=None):
	issue_name = doc.custom_origin_issue
	if not issue_name:
		title = _subject_title(doc.custom_service_subject)
		issue = frappe.get_doc({
			"doctype": "Issue",
			"customer": doc.customer,
			"custom_service_subject": doc.custom_service_subject,
			"subject": title,
			"description": _("Atendimento criado automaticamente a partir da ordem de serviço {0}.").format(doc.name),
			"status": "Open",
		})
		issue.insert(ignore_permissions=True)
		issue_name = issue.name
		doc.custom_origin_issue = issue_name
		frappe.db.set_value("Maintenance Visit", doc.name, "custom_origin_issue", issue_name, update_modified=False)

	frappe.db.set_value(
		"Issue", issue_name, "custom_generated_service_order", doc.name, update_modified=False
	)
	_add_customer_activity(
		doc.customer,
		_("Ordem de serviço {0} criada a partir do atendimento {1}.").format(
			get_link_to_form("Maintenance Visit", doc.name, doc.name),
			get_link_to_form("Issue", issue_name, issue_name),
		),
	)


@frappe.whitelist()
def reopen_service_order(name):
	doc = frappe.get_doc("Maintenance Visit", name)
	doc.check_permission("cancel")
	if doc.docstatus != 1:
		frappe.throw(_("Somente uma ordem de serviço enviada pode ser reaberta."))
	if frappe.db.exists("Maintenance Visit", {"amended_from": doc.name}):
		frappe.throw(_("Esta ordem de serviço já possui uma versão reaberta."))

	doc.cancel()
	amendment = frappe.copy_doc(doc)
	amendment.docstatus = 0
	amendment.amended_from = doc.name
	amendment.completion_status = "Partially Completed"
	amendment.status = "Draft"
	amendment.insert()
	return amendment.name
