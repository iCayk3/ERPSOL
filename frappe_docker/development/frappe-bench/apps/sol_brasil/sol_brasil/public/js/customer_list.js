frappe.listview_settings["Customer"] = frappe.listview_settings["Customer"] || {};

const sol_customer_previous_onload = frappe.listview_settings["Customer"].onload;

frappe.listview_settings["Customer"].onload = function (listview) {
	frappe.breadcrumbs.set_doctype_module("Customer", "SOL Brasil");
	listview.page.set_primary_action(__("Cadastro completo"), () => {
		frappe.model.with_doctype("Customer", () => {
			const customer = frappe.model.get_new_doc("Customer");
			frappe.set_route("Form", "Customer", customer.name);
		});
	});
	listview.page.add_inner_button(__("Cadastro resumido (Lead)"), () => sol_open_lead_dialog());
	listview.page.add_inner_button(__("Ver futuros clientes"), () => frappe.set_route("List", "Lead"));
	if (sol_customer_previous_onload) {
		sol_customer_previous_onload(listview);
	}
};

function sol_open_lead_dialog() {
	const dialog = new frappe.ui.Dialog({
		title: __("Cadastro resumido de futuro cliente"),
		fields: [
			{ fieldname: "first_name", fieldtype: "Data", label: __("Nome"), reqd: 1 },
			{ fieldname: "mobile_no", fieldtype: "Data", label: __("Celular"), reqd: 1 },
			{ fieldname: "email_id", fieldtype: "Data", label: __("E-mail"), options: "Email" },
			{ fieldname: "custom_tax_document", fieldtype: "Data", label: __("CPF / CNPJ") },
			{ fieldname: "custom_interest_plan", fieldtype: "Link", label: __("Plano de interesse"), options: "Subscription Plan" },
			{ fieldname: "custom_installation_region", fieldtype: "Data", label: __("Bairro / região da instalação") },
		],
		primary_action_label: __("Salvar futuro cliente"),
		primary_action(values) {
			frappe.call({
				method: "frappe.client.insert",
				args: { doc: { doctype: "Lead", status: "Lead", ...values } },
				freeze: true,
				callback(response) {
					dialog.hide();
					frappe.show_alert({ message: __("Futuro cliente cadastrado como Lead."), indicator: "green" });
					frappe.set_route("Form", "Lead", response.message.name);
				},
			});
		},
	});
	dialog.show();
}
