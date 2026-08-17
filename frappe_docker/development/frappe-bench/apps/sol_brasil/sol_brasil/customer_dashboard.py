from frappe import _


def get_dashboard_data(data):
	data.transactions = [
		{"label": _("Serviços do cliente"), "items": ["Subscription", "Asset"]},
		{"label": _("Financeiro"), "items": ["Sales Invoice", "Payment Entry", "Dunning"]},
		{
			"label": _("Atendimento e instalação"),
			"items": ["Issue", "Installation Note", "Maintenance Visit"],
		},
	]
	return data
