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

frappe.ui.form.on("Subscription", {
	setup(frm) {
		sol_configure_subscription_address(frm);
	},
	refresh(frm) {
		sol_configure_subscription_address(frm);
		sol_fill_single_customer_address(frm);
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
