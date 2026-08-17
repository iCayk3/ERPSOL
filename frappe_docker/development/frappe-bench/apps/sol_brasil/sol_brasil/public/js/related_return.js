window.sol_customer_navigation = window.sol_customer_navigation || {
	key: "sol_brasil:return_to_customer",
	start(customer, target_doctype) {
		sessionStorage.setItem(this.key, JSON.stringify({ customer, target_doctype, created_at: Date.now() }));
	},
	consume(frm) {
		// Em documentos submetíveis (fatura/recebimento), concluir significa enviar,
		// não apenas guardar o rascunho.
		if (frm.meta.is_submittable && frm.doc.docstatus === 0) return;
		let context;
		try {
			context = JSON.parse(sessionStorage.getItem(this.key) || "null");
		} catch (error) {
			sessionStorage.removeItem(this.key);
			return;
		}
		if (!context || context.target_doctype !== frm.doctype || Date.now() - context.created_at > 7200000) return;
		frappe.call("sol_brasil.lead.should_return_to_customer").then(({ message }) => {
			sessionStorage.removeItem(this.key);
			if (!message) return;
			frappe.set_route("Form", "Customer", context.customer);
		});
	},
};

["Subscription", "Sales Invoice", "Issue", "Asset", "Maintenance Visit", "Payment Entry"].forEach((doctype) => {
	frappe.ui.form.on(doctype, {
		after_save(frm) {
			window.sol_customer_navigation.consume(frm);
		},
	});
});
