window.sol_customer_navigation = window.sol_customer_navigation || {
	key: "sol_brasil:return_to_customer",
	start(customer, target_doctype) {
		sessionStorage.setItem(this.key, JSON.stringify({ customer, target_doctype, created_at: Date.now() }));
	},
	get_context(target_doctype) {
		let context;
		try {
			context = JSON.parse(sessionStorage.getItem(this.key) || "null");
		} catch (error) {
			sessionStorage.removeItem(this.key);
			return null;
		}
		if (
			!context ||
			context.target_doctype !== target_doctype ||
			Date.now() - context.created_at > 7200000
		) {
			return null;
		}
		return context;
	},
	return_to_customer(target_doctype) {
		const context = this.get_context(target_doctype);
		if (!context) return;
		sessionStorage.removeItem(this.key);
		frappe.model.clear_doc("Customer", context.customer);
		frappe.set_route("Form", "Customer", context.customer);
	},
	consume(frm) {
		// Em documentos submetíveis (fatura/recebimento), concluir significa enviar,
		// não apenas guardar o rascunho.
		if (frm.meta.is_submittable && frm.doc.docstatus === 0) return;
		const context = this.get_context(frm.doctype);
		if (!context) return;
		frappe.call("sol_brasil.lead.should_return_to_customer").then(({ message }) => {
			sessionStorage.removeItem(this.key);
			if (!message) return;
			// A ficha pode continuar em cache enquanto o contrato/fatura registra
			// comentários no servidor. Removê-la força uma nova carga do documento
			// e do docinfo (comentários, versões e demais itens da atividade).
			frappe.model.clear_doc("Customer", context.customer);
			frappe.set_route("Form", "Customer", context.customer);
		});
	},
};

frappe.ui.form.on("Payment Entry", {
	refresh(frm) {
		const context = window.sol_customer_navigation.get_context(frm.doctype);
		if (!context || (frm.doc.party_type === "Customer" && frm.doc.party !== context.customer)) return;
		frm.add_custom_button(__("Voltar ao cliente"), () => {
			window.sol_customer_navigation.return_to_customer(frm.doctype);
		});
	},
});

["Subscription", "Sales Invoice", "Issue", "Asset", "Maintenance Visit", "Payment Entry"].forEach((doctype) => {
	frappe.ui.form.on(doctype, {
		after_save(frm) {
			window.sol_customer_navigation.consume(frm);
		},
	});
});
