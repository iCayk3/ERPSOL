frappe.ui.form.on("OLT", {
	setup(frm) {
		frm.set_query("modelo", () => ({
			filters: {
				brand: frm.doc.fabricante || "",
				disabled: 0,
			},
		}));
	},

	fabricante(frm) {
		if (frm.doc.modelo) {
			frm.set_value("modelo", null);
		}
	},
});
