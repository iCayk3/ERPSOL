frappe.ui.form.on("OLT", {
	setup(frm) {
		frm.set_query("modelo", () => ({
			filters: {
				brand: frm.doc.fabricante || "",
				disabled: 0,
			},
		}));
	},
	refresh(frm) {
		if (frm.is_new()) return;
		sol_set_olt_properties_visibility(frm, Boolean(frm.sol_olt_properties_visible));
		const properties_button = frm.add_custom_button(__("Propriedades da OLT"), () => {
			frm.sol_olt_properties_visible = !frm.sol_olt_properties_visible;
			sol_set_olt_properties_visibility(frm, frm.sol_olt_properties_visible);
			properties_button.text(frm.sol_olt_properties_visible ? __("Ocultar propriedades") : __("Propriedades da OLT"));
		});
		frm.add_custom_button(__("Cadastrar CTO"), () => {
			frappe.new_doc("Caixa de Atendimento", { olt: frm.doc.name });
		});
		sol_load_olt_ctos(frm);
	},

	fabricante(frm) {
		if (frm.doc.modelo) {
			frm.set_value("modelo", null);
		}
	},
});

function sol_set_olt_properties_visibility(frm, visible) {
	[
		"identificacao",
		"situacao",
		"quantidade_slots_pon",
		"pons_por_slot",
		"column_break_identificacao",
		"fabricante",
		"modelo",
		"detalhes_tecnicos_section",
		"numero_serie",
		"ip_gerenciamento",
		"tl1_olt_id",
		"column_break_detalhes",
		"local_instalacao",
		"observacoes",
	].forEach((fieldname) => frm.toggle_display(fieldname, visible));
}

function sol_load_olt_ctos(frm) {
	const wrapper = frm.fields_dict.ctos_panel?.$wrapper;
	if (!wrapper) return;
	wrapper.html(`<div class="text-muted py-3">${__("Carregando CTOs...")}</div>`);
	frappe.call({
		method: "sol_brasil.network.get_olt_ctos",
		args: { olt: frm.doc.name },
		callback: ({ message }) => {
			const rows = message || [];
			wrapper.html(`
				<div class="d-flex justify-content-between align-items-center mb-3">
					<p class="text-muted mb-0">${__("CTOs distribuídas pelos slots e PONs desta OLT.")}</p>
					<button class="btn btn-primary btn-sm sol-new-cto">${__("Cadastrar CTO")}</button>
				</div>
				<div class="table-responsive"><table class="table table-bordered">
					<thead><tr><th>${__("CTO")}</th><th>${__("Slot")}</th><th>${__("PON")}</th><th>${__("Situação")}</th><th>${__("Portas ocupadas")}</th><th>${__("Portas livres")}</th></tr></thead>
					<tbody>${rows.length ? rows.map((row) => `<tr>
						<td><a href="/desk/caixa-de-atendimento/${encodeURIComponent(row.name)}">${frappe.utils.escape_html(row.identificacao || row.name)}</a></td>
						<td>${frappe.utils.escape_html(row.slot || "—")}</td>
						<td>${frappe.utils.escape_html(row.pon || "—")}</td>
						<td>${__(row.situacao || "—")}</td>
						<td>${row.occupied || 0} / ${row.capacidade || 0}</td>
						<td>${row.available || 0}</td>
					</tr>`).join("") : `<tr><td colspan="6" class="text-muted">${__("Nenhuma CTO cadastrada nesta OLT.")}</td></tr>`}</tbody>
				</table></div>`);
			wrapper.find(".sol-new-cto").on("click", () => frappe.new_doc("Caixa de Atendimento", { olt: frm.doc.name }));
		},
	});
}
