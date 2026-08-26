function sol_configure_subscription_address(frm) {
	frm.set_query("custom_installation_address", () => ({
		query: "sol_brasil.subscription.address_query",
		filters: { customer: frm.doc.party_type === "Customer" ? frm.doc.party : "" },
	}));
}

function sol_fill_single_customer_address(frm) {
	if (frm.doc.party_type !== "Customer" || !frm.doc.party || frm.doc.custom_installation_address) return;
	frappe.call({
		method: "sol_brasil.subscription.get_customer_addresses",
		args: { customer: frm.doc.party },
		callback: ({ message }) => {
			if ((message || []).length === 1) {
				frm.set_value("custom_installation_address", message[0].name);
			}
		},
	});
}

function sol_subscription_fiberhome_action(frm, method, freeze_message, args = {}) {
	return frappe.call({
		method: `sol_brasil.fiberhome_tl1.${method}`,
		args: { subscription: frm.doc.name, ...args },
		freeze: true,
		freeze_message,
	});
}

function sol_deauthorize_subscription_onu(frm) {
	const dialog = new frappe.ui.Dialog({
		title: __("Confirmar desautorização da ONU"),
		fields: [
			{ fieldtype: "HTML", options: `<div class="alert alert-danger">${__("Para confirmar, digite exatamente o contrato:")} <b>${frappe.utils.escape_html(frm.doc.name)}</b></div>` },
			{ fieldname: "confirmation", fieldtype: "Data", label: __("Confirmação"), reqd: 1 },
		],
		primary_action_label: __("Desautorizar ONU"),
		primary_action(values) {
			dialog.hide();
			sol_subscription_fiberhome_action(frm, "deauthorize_onu", __("Desautorizando ONU no UNM..."), { confirmation: values.confirmation });
		},
	});
	dialog.show();
}

frappe.ui.form.on("Subscription", {
	setup(frm) {
		sol_configure_subscription_address(frm);
	},
	refresh(frm) {
		sol_configure_subscription_address(frm);
		sol_fill_single_customer_address(frm);
		if (!frm.is_new() && frm.doc.party_type === "Customer") {
			const roles = frappe.user_roles || [];
			const can_query = roles.some((role) => ["Consulta de Rede FiberHome", "Operação de Rede FiberHome", "Administração FiberHome", "System Manager"].includes(role));
			const can_operate = roles.some((role) => ["Operação de Rede FiberHome", "Administração FiberHome", "System Manager"].includes(role));
			if (can_query) {
				frm.add_custom_button(__("Consultar sinal da ONU"), () => sol_subscription_fiberhome_action(frm, "query_signal", __("Consultando potência óptica no UNM...")).then(() => frm.reload_doc()), __("FiberHome"));
			}
			if (can_operate) {
				frm.add_custom_button(__("Autorizar ONU"), () => sol_subscription_fiberhome_action(frm, "authorize_onu", __("Autorizando ONU no UNM...")), __("FiberHome"));
				frm.add_custom_button(__("Desautorizar ONU"), () => sol_deauthorize_subscription_onu(frm), __("FiberHome"));
			}
		}
	},
	party_type(frm) {
		frm.set_value("custom_installation_address", null);
		sol_configure_subscription_address(frm);
	},
	party(frm) {
		frm.set_value("custom_installation_address", null).then(() => {
			sol_configure_subscription_address(frm);
			sol_fill_single_customer_address(frm);
		});
	},
});
