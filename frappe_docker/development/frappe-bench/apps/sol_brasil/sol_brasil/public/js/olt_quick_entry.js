frappe.provide("frappe.ui.form");

frappe.ui.form.OLTQuickEntryForm = class OLTQuickEntryForm extends (
	frappe.ui.form.QuickEntryForm
) {
	render_dialog() {
		super.render_dialog();

		const fabricante = this.dialog.get_field("fabricante");
		const modelo = this.dialog.get_field("modelo");
		if (!fabricante || !modelo) {
			return;
		}

		modelo.get_query = () => ({
			filters: {
				brand: fabricante.get_value() || "",
				disabled: 0,
			},
		});

		fabricante.df.onchange = () => {
			if (modelo.get_value()) {
				modelo.set_value("");
			}
		};
	}
};
