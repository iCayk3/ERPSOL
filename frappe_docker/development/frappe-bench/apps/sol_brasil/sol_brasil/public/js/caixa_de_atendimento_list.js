frappe.listview_settings["Caixa de Atendimento"] = {
	onload(listview) {
		listview.page.add_inner_button(__("Filtrar por OLT/PON"), () => {
			const dialog = new frappe.ui.Dialog({
				title: __("Localizar CTOs"),
				fields: [
					{ fieldname: "olt", fieldtype: "Link", options: "OLT", label: __("OLT"), reqd: 1 },
					{ fieldname: "pon", fieldtype: "Select", label: __("PON"), options: [""] },
				],
				primary_action_label: __("Aplicar filtros"),
				primary_action(values) {
					const filters = [["Caixa de Atendimento", "olt", "=", values.olt]];
					if (values.pon) filters.push(["Caixa de Atendimento", "pon", "=", values.pon]);
					listview.filter_area.add(filters);
					dialog.hide();
				},
			});
			dialog.fields_dict.olt.$input.on("change", () => {
				const olt = dialog.get_value("olt");
				if (!olt) return;
				frappe.db.get_value("OLT", olt, "pons_por_slot").then(({ message }) => {
					const count = Number(message?.pons_por_slot) || 0;
					dialog.set_df_property("pon", "options", ["", ...Array.from({ length: count }, (_, i) => String(i + 1))]);
				});
			});
			dialog.show();
		});
	},
};
