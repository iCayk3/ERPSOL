function sol_configure_service_subject(frm) {
	frm.set_query("custom_service_subject", () => ({ filters: { ativo: 1 } }));
}

function sol_configure_service_answer(frm) {
	const is_closing = ["Resolved", "Closed"].includes(frm.doc.status);
	frm.set_df_property("resolution_details", "label", __("Resposta/conclusão do atendimento"));
	frm.set_df_property(
		"resolution_details",
		"description",
		__("Obrigatória ao resolver ou fechar. Informe o retorno dado, mesmo quando não houver solução.")
	);
	frm.toggle_reqd("resolution_details", is_closing);
}

function sol_go_to_customer(customer) {
	if (!customer) return;
	frappe.model.clear_doc("Customer", customer);
	frappe.set_route("Form", "Customer", customer);
}

function sol_close_service(frm) {
	const dialog = new frappe.ui.Dialog({
		title: __("Fechar atendimento"),
		fields: [{
			fieldname: "answer",
			fieldtype: "Text Editor",
			label: __("Resposta/conclusão do atendimento"),
			description: __("Descreva o retorno dado, mesmo quando o problema não tiver sido solucionado."),
			default: frm.doc.resolution_details || "",
			reqd: 1,
		}],
		primary_action_label: __("Registrar e fechar"),
		primary_action: async (values) => {
			dialog.disable_primary_action();
			try {
				await frm.set_value("resolution_details", values.answer);
				await frm.set_value("status", "Closed");
				await frm.save();
				dialog.hide();
			} catch (error) {
				dialog.enable_primary_action();
				await frm.reload_doc();
			}
		},
	});
	dialog.show();
}

async function sol_reopen_service(frm) {
	try {
		await frm.set_value("status", "Open");
		await frm.save();
	} catch (error) {
		await frm.reload_doc();
	}
}

frappe.ui.form.on("Issue", {
	setup(frm) {
		sol_configure_service_subject(frm);
	},
	refresh(frm) {
		sol_configure_service_subject(frm);
		sol_configure_service_answer(frm);
		frm.remove_custom_button(__("Close"));
		frm.remove_custom_button(__("Reopen"));
		frm.set_df_property("subject", "label", __("Resumo do atendimento"));
		if (!frm.is_new() && frm.doc.status !== "Closed") {
			frm.add_custom_button(__("Fechar atendimento"), () => sol_close_service(frm));
		} else if (!frm.is_new()) {
			frm.add_custom_button(__("Reabrir atendimento"), () => sol_reopen_service(frm));
		}
		if (frm.doc.customer) {
			frm.add_custom_button(
				__("Voltar ao cliente"),
				() => sol_go_to_customer(frm.doc.customer)
			);
		}
		if (!frm.is_new() && frm.doc.customer && !frm.doc.custom_generated_service_order) {
			frm.add_custom_button(__("Gerar OS"), () => {
				window.sol_customer_navigation?.start(frm.doc.customer, "Maintenance Visit");
				frappe.new_doc("Maintenance Visit", {
					customer: frm.doc.customer,
					custom_service_subject: frm.doc.custom_service_subject,
					custom_origin_issue: frm.doc.name,
				});
			});
		}
		if (frm.doc.custom_generated_service_order) {
			frm.add_custom_button(__("Abrir OS"), () => {
				frappe.set_route("Form", "Maintenance Visit", frm.doc.custom_generated_service_order);
			});
		}
	},
	status(frm) {
		sol_configure_service_answer(frm);
	},
});
