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

function sol_related_customer(frm) {
	if (frm.doc.party_type === "Customer" && frm.doc.party) return frm.doc.party;
	if (frm.doc.customer) return frm.doc.customer;
	if (frm.doc.cliente) return frm.doc.cliente;

	const customer_link = (frm.doc.links || []).find(
		(link) => link.link_doctype === "Customer" && link.link_name
	);
	return customer_link?.link_name || window.sol_customer_navigation.get_context(frm.doctype)?.customer;
}

function sol_go_back_to_customer(customer) {
	if (!customer) return;
	sessionStorage.removeItem(window.sol_customer_navigation.key);
	frappe.model.clear_doc("Customer", customer);
	frappe.set_route("Form", "Customer", customer);
}

function sol_set_customer_origin_breadcrumb(frm, customer) {
	if (!customer || frm.is_new()) return;
	const set_breadcrumb = (customer_label) => {
		// A navegação padrão mostra apenas o módulo/lista do documento. Para os
		// registros do atendimento, a ficha do cliente é a origem mais útil.
		frappe.breadcrumbs.add({
			type: "Custom",
			route: "/desk/customer",
			label: __("Clientes"),
		});
		frappe.breadcrumbs.append_breadcrumb_element(
			`/desk/customer/${encodeURIComponent(customer)}`,
			frappe.utils.escape_html(customer_label || customer),
			"title-text"
		);
		frappe.breadcrumbs.append_breadcrumb_element(
			"",
			frappe.utils.escape_html(frappe.model.get_doc_title(frm.doc) || frm.doc.name),
			"title-text-form"
		);
		frappe.breadcrumbs.$breadcrumbs.find("li:last").addClass("disabled");
	};

	set_breadcrumb(customer);
	frappe.db.get_value("Customer", customer, "customer_name").then(({ message }) => {
		if (cur_frm === frm && sol_related_customer(frm) === customer) {
			set_breadcrumb(message?.customer_name || customer);
		}
	});
}

function sol_add_customer_return_navigation(frm) {
	const customer = sol_related_customer(frm);
	if (!customer) return;
	frm.add_custom_button(__("Voltar à ficha do cliente"), () => sol_go_back_to_customer(customer));
	setTimeout(() => sol_set_customer_origin_breadcrumb(frm, customer), 0);
}

[
	"Subscription",
	"Sales Invoice",
	"Issue",
	"Asset",
	"Maintenance Visit",
	"Payment Entry",
	"Address",
	"Contact",
	"Acesso PPPoE",
	"Operação FiberHome",
].forEach((doctype) => {
	frappe.ui.form.on(doctype, {
		refresh(frm) {
			sol_add_customer_return_navigation(frm);
		},
	});
});

["Subscription", "Sales Invoice", "Issue", "Asset", "Maintenance Visit", "Payment Entry"].forEach((doctype) => {
	frappe.ui.form.on(doctype, {
		after_save(frm) {
			window.sol_customer_navigation.consume(frm);
		},
	});
});
