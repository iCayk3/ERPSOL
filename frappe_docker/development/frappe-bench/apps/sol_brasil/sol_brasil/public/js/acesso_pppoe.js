frappe.ui.form.on("Acesso PPPoE", {
	setup(frm) {
		frm.set_query("contrato", () => ({
			filters: {
				party_type: "Customer",
				party: frm.doc.cliente || "",
				status: ["not in", ["Cancelled", "Completed"]],
			},
		}));
		frm.set_query("nas_radius", () => ({
			filters: { ativo: 1 },
		}));
	},

	cliente(frm) {
		if (frm.doc.contrato) frm.set_value("contrato", null);
	},
});
