import frappe
from frappe import _
from frappe.utils import nowdate


def complete_checked_dependencies(doc, method=None):
	"""Treat checked dependency rows as a simple completion checklist."""
	for row in doc.get("depends_on") or []:
		if not row.get("custom_completed") or not row.task or row.task == doc.name:
			continue

		dependency = frappe.get_doc("Task", row.task)
		if dependency.status in ("Completed", "Cancelled"):
			continue

		dependency.status = "Completed"
		dependency.completed_on = nowdate()
		if dependency.meta.has_field("completed_by"):
			dependency.completed_by = frappe.session.user
		try:
			dependency.save()
		except frappe.ValidationError:
			frappe.throw(
				_("Não foi possível concluir o item {0}. Abra a tarefa vinculada e verifique os campos obrigatórios.").format(
					frappe.bold(row.task)
				),
				title=_("Item do checklist pendente"),
			)
