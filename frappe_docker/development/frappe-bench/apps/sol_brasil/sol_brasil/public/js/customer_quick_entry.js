frappe.provide("frappe.ui.form");

frappe.ui.form.CustomerQuickEntryForm = class SolCustomerQuickEntryForm extends (
	frappe.ui.form.ContactAddressQuickEntryForm
) {
	get_title() {
		return __("Cadastro resumido de futuro cliente");
	}

	set_meta_and_mandatory_fields() {
		super.set_meta_and_mandatory_fields();
		this.docfields = this.docfields.map((field) => {
			const copy = { ...field };
			if (copy.fieldname === "custom_tax_document") {
				copy.reqd = 0;
				copy.label = this.doc.customer_type === "Company" ? __("CNPJ") : __("CPF");
			}
			return copy;
		});
	}

	register_primary_action() {
		this.set_primary_action(__("Salvar como futuro cliente"), () => {
			if (this.dialog.working) return;
			const values = this.dialog.get_values();
			if (!values) return;

			this.dialog.working = true;
			frappe.call({
				method: "sol_brasil.lead.create_from_customer_quick_entry",
				args: { data: values },
				freeze: true,
				callback: (response) => {
					this.dialog.hide();
					frappe.show_alert({
						message: __("Futuro cliente salvo na lista de Leads."),
						indicator: "green",
					});
					frappe.set_route("Form", "Lead", response.message.name);
				},
				always: () => {
					this.dialog.working = false;
				},
			});
		});
	}
};
