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

function sol_topology_options(total) {
	return ["", ...Array.from({ length: Number(total) || 0 }, (_, index) => String(index + 1))];
}

function sol_configure_subscription_topology(frm, clear_from = "") {
	if (clear_from === "olt") {
		frm.set_value({ custom_olt_slot_select: "", custom_pon_select: "", custom_pon_port: "", custom_installation_box_link: "", custom_cto_port: "" });
	} else if (clear_from === "slot") {
		frm.set_value({ custom_pon_select: "", custom_pon_port: "", custom_installation_box_link: "", custom_cto_port: "" });
	} else if (clear_from === "pon") {
		frm.set_value({ custom_pon_port: frm.doc.custom_pon_select || "", custom_installation_box_link: "", custom_cto_port: "" });
	}

	frm.set_query("custom_installation_box_link", () => ({
		filters: {
			olt: frm.doc.custom_olt || "",
			slot: frm.doc.custom_olt_slot_select || "",
			pon: frm.doc.custom_pon_select || "",
			situacao: "Ativa",
		},
	}));

	if (!frm.doc.custom_olt) {
		frm.set_df_property("custom_olt_slot_select", "options", [""]);
		frm.set_df_property("custom_pon_select", "options", [""]);
		return;
	}

	frappe.db.get_value("OLT", frm.doc.custom_olt, ["quantidade_slots_pon", "pons_por_slot"]).then(({ message }) => {
		frm.set_df_property("custom_olt_slot_select", "options", sol_topology_options(message?.quantidade_slots_pon));
		frm.set_df_property("custom_pon_select", "options", sol_topology_options(message?.pons_por_slot));
		if (!frm.doc.custom_olt_slot_select && /^\d+$/.test(frm.doc.custom_olt_slot || "")) {
			frm.set_value("custom_olt_slot_select", frm.doc.custom_olt_slot);
		}
		const legacy_pon = frm.doc.custom_pon_port || frm.doc.custom_pon || "";
		if (!frm.doc.custom_pon_select && /^\d+$/.test(legacy_pon)) {
			frm.set_value("custom_pon_select", legacy_pon);
		}
		frm.refresh_fields(["custom_olt_slot_select", "custom_pon_select"]);
	});
}

function sol_load_available_cto_ports(frm, clear_value = false) {
	if (clear_value) frm.set_value("custom_cto_port", "");
	if (!frm.doc.custom_installation_box_link) {
		frm.set_df_property("custom_cto_port", "options", [""]);
		frm.set_df_property("custom_cto_port", "description", __("Selecione primeiro uma CTO."));
		return;
	}

	frappe.call({
		method: "sol_brasil.subscription.get_available_cto_ports",
		args: {
			cto: frm.doc.custom_installation_box_link,
			subscription: frm.doc.name,
		},
		callback: ({ message }) => {
			const available = message?.available || [];
			const current = Number(frm.doc.custom_cto_port) || 0;
			const options = [...new Set([...(current ? [current] : []), ...available])].sort((a, b) => a - b);
			frm.set_df_property("custom_cto_port", "options", ["", ...options.map(String)]);
			frm.set_df_property(
				"custom_cto_port",
				"description",
				__("{0} de {1} portas disponíveis.", [available.length, message?.capacity || 0])
			);
			frm.refresh_field("custom_cto_port");
		},
	});
}

function sol_reorder_subscription_tabs(frm) {
	const tabs = frm.layout?.tabs || [];
	const provider_tab = tabs.find((tab) => tab.df?.fieldname === "custom_provider_tab");
	if (!provider_tab) return;

	provider_tab.tab_link.prependTo(frm.layout.tab_link_container);
	provider_tab.wrapper.prependTo(frm.layout.tabs_content);
	frm.layout.tabs = [provider_tab, ...tabs.filter((tab) => tab !== provider_tab)];

	if (!frm.sol_provider_tab_initialized) {
		provider_tab.set_active();
		frm.sol_provider_tab_initialized = true;
	}
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
		sol_configure_subscription_topology(frm);
		sol_load_available_cto_ports(frm);
	},
	refresh(frm) {
		sol_configure_subscription_address(frm);
		sol_fill_single_customer_address(frm);
		sol_configure_subscription_topology(frm);
		sol_load_available_cto_ports(frm);
		setTimeout(() => sol_reorder_subscription_tabs(frm), 0);
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
	custom_olt(frm) {
		sol_configure_subscription_topology(frm, "olt");
	},
	custom_olt_slot_select(frm) {
		sol_configure_subscription_topology(frm, "slot");
	},
	custom_pon_select(frm) {
		sol_configure_subscription_topology(frm, "pon");
	},
	custom_installation_box_link(frm) {
		sol_load_available_cto_ports(frm, true);
	},
});
