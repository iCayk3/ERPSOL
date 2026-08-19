function sol_refresh_customer_after_reference_save(frm) {
	const customer = (frm.doc.links || []).find((link) => link.link_doctype === "Customer")?.link_name;
	const customerForm = window.cur_frm;
	if (!customer || !customerForm || customerForm.doctype !== "Customer" || customerForm.doc.name !== customer) return;
	if (!customerForm.is_dirty()) {
		setTimeout(() => customerForm.reload_doc(), 150);
	}
}

["Address", "Contact"].forEach((doctype) => {
	frappe.ui.form.on(doctype, {
		after_save(frm) {
			sol_refresh_customer_after_reference_save(frm);
		},
	});
});
