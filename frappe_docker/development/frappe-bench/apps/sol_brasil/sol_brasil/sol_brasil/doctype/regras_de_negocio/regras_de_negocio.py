import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import cint


class RegrasdeNegocio(Document):
	def validate(self):
		block_days = cint(self.block_after_days)
		suspend_days = cint(self.suspend_after_days)
		if block_days < 1:
			frappe.throw(_("O bloqueio deve ocorrer após pelo menos um dia de atraso."))
		invalid_plan = frappe.db.get_value(
			"Subscription Plan",
			{"custom_enable_overdue_reduction": 1, "custom_reduce_after_days": [">", block_days]},
			"name",
		)
		if invalid_plan:
			frappe.throw(
				_("O bloqueio não pode ocorrer antes da redução configurada no plano {0}.").format(
					frappe.bold(invalid_plan)
				)
			)
		if suspend_days <= block_days:
			frappe.throw(_("O prazo de suspensão deve ser maior que o prazo de bloqueio."))

	def on_update(self):
		frappe.enqueue(
			"sol_brasil.business_rules.recalculate_all_contract_statuses",
			queue="long",
			enqueue_after_commit=True,
		)
