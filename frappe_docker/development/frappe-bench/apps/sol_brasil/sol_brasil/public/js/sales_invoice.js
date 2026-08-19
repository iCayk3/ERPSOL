function sol_get_items_from_contract(frm) {
	frappe.prompt(
		[{
			fieldname: "contract",
			fieldtype: "Link",
			options: "Subscription",
			label: __("Contrato"),
			reqd: 1,
			get_query: () => ({
				filters: {
					party_type: "Customer",
					...(frm.doc.customer ? { party: frm.doc.customer } : {}),
					status: ["not in", ["Cancelled", "Completed"]],
					...(frm.doc.company ? { company: frm.doc.company } : {}),
				},
			}),
		}],
		(values) => {
			erpnext.utils.map_current_doc({
				method: "sol_brasil.subscription.map_contract_to_sales_invoice",
				source_name: values.contract,
			});
		},
		__("Obter itens do contrato"),
		__("Carregar contrato")
	);
}

frappe.ui.form.on("Sales Invoice", {
	refresh(frm) {
		frm.set_df_property("subscription", "label", __("Contrato vinculado"));
		frm.set_query("subscription", () => ({
			filters: {
				party_type: "Customer",
				...(frm.doc.customer ? { party: frm.doc.customer } : {}),
			},
		}));
		if (frm.doc.docstatus === 0 && !frm.doc.is_return) {
			frm.add_custom_button(
				__("Contrato"),
				() => sol_get_items_from_contract(frm),
				__("Get Items From")
			);
		}
	},
});
