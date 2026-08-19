frappe.ui.form.on("Maintenance Visit", {
	setup(frm) {
		frm.set_query("custom_service_subject", () => ({ filters: { ativo: 1 } }));
		frm.set_query("custom_provider_service", "purposes", () => ({ filters: { ativo: 1 } }));
	},
	refresh(frm) {
		frm.set_query("custom_service_subject", () => ({ filters: { ativo: 1 } }));
		frm.set_query("custom_provider_service", "purposes", () => ({ filters: { ativo: 1 } }));
		if (frm.doc.customer) {
			frm.add_custom_button(__("Voltar ao cliente"), () => {
				frappe.model.clear_doc("Customer", frm.doc.customer);
				frappe.set_route("Form", "Customer", frm.doc.customer);
			});
		}
		if (frm.doc.custom_origin_issue) {
			frm.add_custom_button(__("Abrir atendimento"), () => {
				frappe.set_route("Form", "Issue", frm.doc.custom_origin_issue);
			});
		}
	},
});

frappe.ui.form.on("Maintenance Visit Purpose", {
	custom_provider_service(frm, cdt, cdn) {
		const row = locals[cdt][cdn];
		if (!row.custom_provider_service) return;
		frappe.db.get_value("Servico do Provedor", row.custom_provider_service, ["servico", "descricao"])
			.then(({ message }) => {
				if (!message) return;
				frappe.model.set_value(cdt, cdn, "item_name", message.servico);
				if (!row.description && message.descricao) {
					frappe.model.set_value(cdt, cdn, "description", message.descricao);
				}
			});
	},
});
