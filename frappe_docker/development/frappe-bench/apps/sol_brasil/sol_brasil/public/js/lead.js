frappe.ui.form.on("Lead", {
	refresh(frm) {
		if (frm.is_new()) return;

		frm.remove_custom_button(__("Customer"), __("Create"));
		frm.add_custom_button(__("Registrar comentário interno"), () => {
			frappe.prompt(
				[{ fieldname: "content", fieldtype: "Small Text", label: __("Comentário interno"), reqd: 1 }],
				(values) => frappe.call({
					method: "sol_brasil.customer.add_internal_comment",
					args: { reference_doctype: "Lead", reference_name: frm.doc.name, content: values.content },
					callback: () => {
						frappe.show_alert({ message: __("Comentário registrado no histórico interno."), indicator: "green" });
						frm.reload_doc();
					},
				}),
				__("Registrar comentário interno"),
				__("Registrar")
			);
		}, __("Histórico"));
		if (!frm.doc.__onload?.is_customer) {
			frm.add_custom_button(__("Ver contratos do Lead"), () => {
				frappe.set_route("List", "Contrato Preliminar", { lead: frm.doc.name });
			}, __("Contratos"));
			frappe.call("sol_brasil.lead.get_contract_configuration").then(({ message }) => {
				const configured = message?.lead_contract_flow || "Permitir escolha no Lead";
				const flows = configured === "Permitir escolha no Lead"
					? ["Pré-pagamento", "Pós-pagamento"]
					: [configured];
				flows.forEach((flow) => {
					frm.add_custom_button(__(`Contrato ${flow.toLowerCase()}`), () => {
						frappe.new_doc("Contrato Preliminar", {
							lead: frm.doc.name,
							contract_flow: flow,
							subscription_plan: frm.doc.custom_interest_plan,
						});
					}, __("Contratos"));
				});
			});
			frm.add_custom_button(__("Converter em cliente definitivo"), () => {
				frappe.model.open_mapped_doc({
					method: "sol_brasil.lead.make_customer",
					frm,
				});
			}, __("Conversão"));
		}
	},
});
