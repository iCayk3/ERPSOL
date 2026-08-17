frappe.ui.form.on("Contrato Preliminar", {
	refresh(frm) {
		if (
			!frm.is_new()
			&& frm.doc.contract_flow === "Pré-pagamento"
			&& frm.doc.contract_status === "Aguardando pagamento"
		) {
			frm.add_custom_button(__("Confirmar pagamento"), () => {
				frappe.prompt(
					[
						{ fieldname: "payment_date", fieldtype: "Date", label: __("Data do pagamento"), default: frappe.datetime.get_today(), reqd: 1 },
						{ fieldname: "payment_reference", fieldtype: "Data", label: __("Referência/comprovante"), reqd: 1 },
					],
					(values) => {
						frm.set_value(values).then(() => frm.save());
					},
					__("Confirmar pagamento inicial"),
					__("Confirmar")
				);
			});
		}
	},

	after_save(frm) {
		if (frm.doc.lead) {
			frappe.set_route("Form", "Lead", frm.doc.lead);
		}
	},
});
