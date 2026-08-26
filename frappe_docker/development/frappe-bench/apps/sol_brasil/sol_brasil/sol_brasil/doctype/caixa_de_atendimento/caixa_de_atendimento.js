function sol_number_options(total) {
	return ["", ...Array.from({ length: Number(total) || 0 }, (_, index) => String(index + 1))];
}

function sol_configure_cto_topology(frm, clear_values = false) {
	if (clear_values) {
		frm.set_value({ slot: "", pon: "" });
	}
	if (!frm.doc.olt) {
		frm.set_df_property("slot", "options", [""]);
		frm.set_df_property("pon", "options", [""]);
		return;
	}
	frappe.db.get_value("OLT", frm.doc.olt, ["quantidade_slots_pon", "pons_por_slot"]).then(({ message }) => {
		frm.set_df_property("slot", "options", sol_number_options(message?.quantidade_slots_pon));
		frm.set_df_property("pon", "options", sol_number_options(message?.pons_por_slot));
		frm.refresh_fields(["slot", "pon"]);
	});
}

frappe.ui.form.on("Caixa de Atendimento", {
	setup(frm) {
		sol_configure_cto_topology(frm);
	},
	refresh(frm) {
		sol_configure_cto_topology(frm);
		if (frm.is_new()) return;
		frm.add_custom_button(__("Adicionar cliente"), () => sol_add_customer_to_cto(frm));
		frm.add_custom_button(__("Voltar à OLT"), () => frappe.set_route("Form", "OLT", frm.doc.olt));
		sol_load_cto_occupants(frm);
	},
	olt(frm) {
		sol_configure_cto_topology(frm, true);
	},
});

function sol_add_customer_to_cto(frm) {
	frappe.prompt(
		[{ fieldname: "customer", fieldtype: "Link", options: "Customer", label: __("Cliente"), reqd: 1 }],
		(values) => frappe.new_doc("Subscription", {
			party_type: "Customer",
			party: values.customer,
			custom_olt: frm.doc.olt,
			custom_olt_slot_select: frm.doc.slot,
			custom_pon_select: frm.doc.pon,
			custom_installation_box_link: frm.doc.name,
		}),
		__("Adicionar cliente à CTO"),
		__("Criar contrato")
	);
}

function sol_load_cto_occupants(frm) {
	const wrapper = frm.fields_dict.occupants_panel?.$wrapper;
	if (!wrapper) return;
	wrapper.html(`<div class="text-muted py-3">${__("Carregando ocupantes...")}</div>`);
	frappe.call({
		method: "sol_brasil.network.get_cto_occupants",
		args: { cto: frm.doc.name },
		callback: ({ message }) => {
			const rows = message || [];
			wrapper.html(`
				<div class="d-flex justify-content-between align-items-center mb-3">
					<p class="text-muted mb-0">${__("Clientes com PPPoE ocupando portas desta CTO.")}</p>
					<button class="btn btn-primary btn-sm sol-add-customer">${__("Adicionar cliente")}</button>
				</div>
				<div class="table-responsive"><table class="table table-bordered">
					<thead><tr><th>${__("Porta")}</th><th>${__("Cliente")}</th><th>${__("Contrato")}</th><th>${__("Usuário PPPoE")}</th><th>${__("Conexão")}</th></tr></thead>
					<tbody>${rows.length ? rows.map((row) => `<tr>
						<td>${frappe.utils.escape_html(row.custom_cto_port || "—")}</td>
						<td><a href="/desk/customer/${encodeURIComponent(row.party)}">${frappe.utils.escape_html(row.party)}</a></td>
						<td><a href="/desk/subscription/${encodeURIComponent(row.name)}">${frappe.utils.escape_html(row.name)}</a></td>
						<td>${frappe.utils.escape_html(row.custom_pppoe_username || "—")}</td>
						<td>${__(row.custom_connection_status || "—")}</td>
					</tr>`).join("") : `<tr><td colspan="5" class="text-muted">${__("Nenhuma porta ocupada nesta CTO.")}</td></tr>`}</tbody>
				</table></div>`);
			wrapper.find(".sol-add-customer").on("click", () => sol_add_customer_to_cto(frm));
		},
	});
}
