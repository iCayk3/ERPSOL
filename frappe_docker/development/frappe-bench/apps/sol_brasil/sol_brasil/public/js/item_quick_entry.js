frappe.provide("frappe.ui.form");

frappe.ui.form.ItemQuickEntryForm = class ItemQuickEntryForm extends (
	frappe.ui.form.QuickEntryForm
) {
	render_dialog() {
		super.render_dialog();

		const controlar_estoque = this.dialog.get_field("is_stock_item");
		const ativo_imobilizado = this.dialog.get_field("is_fixed_asset");
		if (!controlar_estoque || !ativo_imobilizado) {
			return;
		}

		controlar_estoque.df.onchange = () => {
			if (controlar_estoque.get_value() && ativo_imobilizado.get_value()) {
				ativo_imobilizado.set_value(0);
			}
			this.refresh_dependency();
		};

		ativo_imobilizado.df.onchange = () => {
			if (ativo_imobilizado.get_value() && controlar_estoque.get_value()) {
				controlar_estoque.set_value(0);
				frappe.show_alert({
					message: __("Controlar estoque foi desmarcado porque o item é um ativo imobilizado."),
					indicator: "blue",
				});
			}
			this.refresh_dependency();
		};
	}
};
