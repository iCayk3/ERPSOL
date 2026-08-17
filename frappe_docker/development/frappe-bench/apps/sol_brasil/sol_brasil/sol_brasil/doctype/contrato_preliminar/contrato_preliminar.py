import frappe
from frappe.model.document import Document
from frappe.utils import today


class ContratoPreliminar(Document):
	def validate(self):
		settings = frappe.get_single("Configurações do Provedor")
		configured_flow = settings.lead_contract_flow
		if configured_flow in ("Pré-pagamento", "Pós-pagamento") and self.contract_flow != configured_flow:
			frappe.throw(f"O provedor está configurado para utilizar somente contratos {configured_flow.lower()}.")

		if self.contract_flow == "Pós-pagamento" and self.contract_status not in ("Convertido", "Cancelado"):
			self.contract_status = "Pronto para conversão"
		elif self.contract_flow == "Pré-pagamento" and self.contract_status not in ("Convertido", "Cancelado"):
			self.contract_status = "Pago" if self.payment_date else "Aguardando pagamento"

		if not self.start_date:
			self.start_date = today()

	def on_update(self):
		if self.lead and self.subscription_plan:
			frappe.db.set_value("Lead", self.lead, "custom_interest_plan", self.subscription_plan, update_modified=False)
