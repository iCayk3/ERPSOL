frappe.ui.form.on("Configurações FiberHome UNM", {
	refresh(frm) {
		if (frm.is_dirty()) {
			return;
		}

		frm.add_custom_button(__("Testar conexão"), () => {
			frappe.call({
				method: "sol_brasil.fiberhome_tl1.test_connection",
				freeze: true,
				freeze_message: __("Conectando e autenticando no UNM..."),
			}).then(({ message }) => {
				frappe.msgprint({
					title: __("Conexão realizada"),
					message: __(`O login TL1 foi aceito pelo UNM em ${message.latency_ms} ms.`),
					indicator: "green",
				});
			});
		}, __("FiberHome"));
	},
});
