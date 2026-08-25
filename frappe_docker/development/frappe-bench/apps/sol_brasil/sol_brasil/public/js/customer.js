function sol_only_digits(value) {
	return (value || "").replace(/\D/g, "");
}

function sol_format_document(value) {
	const digits = sol_only_digits(value).slice(0, 14);
	if (digits.length <= 11) {
		return digits
			.replace(/(\d{3})(\d)/, "$1.$2")
			.replace(/(\d{3})(\d)/, "$1.$2")
			.replace(/(\d{3})(\d{1,2})$/, "$1-$2");
	}
	return digits
		.replace(/^(\d{2})(\d)/, "$1.$2")
		.replace(/^(\d{2})\.(\d{3})(\d)/, "$1.$2.$3")
		.replace(/\.(\d{3})(\d)/, ".$1/$2")
		.replace(/(\d{4})(\d{1,2})$/, "$1-$2");
}

function sol_refresh_customer_tax_fields(frm) {
	const is_individual = frm.doc.customer_type === "Individual";
	frm.set_df_property("custom_tax_document", "label", is_individual ? "CPF" : "CNPJ");
	frm.set_df_property("custom_tax_document", "description", `Informe um ${is_individual ? "CPF" : "CNPJ"} válido.`);
	frm.toggle_reqd("custom_tax_document", true);
	frm.toggle_display("custom_icms_taxpayer_type", !is_individual);
}

function sol_set_customer_breadcrumb(frm) {
	frappe.breadcrumbs.add({
		type: "Custom",
		route: "/desk/customer",
		label: __("Cliente"),
	});

	if (!frm.is_new()) {
		frappe.breadcrumbs.append_breadcrumb_element(
			"",
			frappe.utils.escape_html(frm.doc.customer_name || frm.doc.name),
			"title-text-form"
		);
	}
}

function sol_reorder_customer_tabs(frm) {
	const wrapper = frm.wrapper;
	const teamTab = wrapper.querySelector('[data-fieldname="sales_team_tab"]');
	if (teamTab) {
		const teamItem = teamTab.closest("li, .nav-item") || teamTab;
		teamItem.style.display = "none";
	}
	const serviceTab = wrapper.querySelector('[data-fieldname="custom_service_tab"]');
	const relationshipsTab = wrapper.querySelector('[data-fieldname="connections_tab"]');
	if (!serviceTab || !relationshipsTab) return;

	const serviceItem = serviceTab.closest("li, .nav-item") || serviceTab;
	const relationshipsItem = relationshipsTab.closest("li, .nav-item") || relationshipsTab;
	if (serviceItem.parentElement && serviceItem.parentElement === relationshipsItem.parentElement) {
		serviceItem.parentElement.insertBefore(relationshipsItem, serviceItem.nextSibling);
	}
}

function sol_paginate_customer_timeline(frm, reset_page = false) {
	const timeline = frm.timeline;
	const wrapper = timeline?.timeline_items_wrapper;
	if (!wrapper?.length) return;

	const page_size = 10;
	const items = wrapper.children(".timeline-item");
	const total = items.length;
	const total_pages = Math.max(1, Math.ceil(total / page_size));
	if (reset_page || !frm.sol_timeline_page) frm.sol_timeline_page = 1;
	frm.sol_timeline_page = Math.min(frm.sol_timeline_page, total_pages);

	const start = (frm.sol_timeline_page - 1) * page_size;
	const end = Math.min(start + page_size, total);
	items.hide().slice(start, end).show();

	let pagination = timeline.timeline_wrapper.children(".sol-timeline-pagination");
	if (!pagination.length) {
		pagination = $(`
			<div class="sol-timeline-pagination d-flex justify-content-between align-items-center mt-3 mb-4">
				<span class="text-muted sol-timeline-range"></span>
				<div class="btn-group btn-group-sm">
					<button class="btn btn-default sol-timeline-previous">${__("Anterior")}</button>
					<button class="btn btn-default sol-timeline-next">${__("Próxima")}</button>
				</div>
			</div>`);
		timeline.timeline_wrapper.append(pagination);
		pagination.find(".sol-timeline-previous").on("click", () => {
			frm.sol_timeline_page -= 1;
			sol_paginate_customer_timeline(frm);
		});
		pagination.find(".sol-timeline-next").on("click", () => {
			frm.sol_timeline_page += 1;
			sol_paginate_customer_timeline(frm);
		});
	}

	pagination.toggle(total > page_size);
	pagination.find(".sol-timeline-range").text(
		__("Atividades {0}–{1} de {2}", [total ? start + 1 : 0, end, total])
	);
	pagination.find(".sol-timeline-previous").prop("disabled", frm.sol_timeline_page === 1);
	pagination.find(".sol-timeline-next").prop("disabled", frm.sol_timeline_page === total_pages);
}

function sol_setup_customer_timeline_pagination(frm) {
	const wrapper = frm.timeline?.timeline_items_wrapper?.get(0);
	if (!wrapper) return;

	if (frm.sol_timeline_observer) frm.sol_timeline_observer.disconnect();
	frm.sol_timeline_observer = new MutationObserver(() => {
		clearTimeout(frm.sol_timeline_pagination_timer);
		frm.sol_timeline_pagination_timer = setTimeout(
			() => sol_paginate_customer_timeline(frm, true),
			0
		);
	});
	frm.sol_timeline_observer.observe(wrapper, { childList: true });
	sol_paginate_customer_timeline(frm, true);
}

function sol_watch_customer_references(frm) {
	if (window.sol_customer_reference_listener_registered) return;
	window.sol_customer_reference_listener_registered = true;
	frappe.realtime.on("sol_customer_reference_updated", (message) => {
		const activeForm = window.cur_frm;
		if (!activeForm || activeForm.doctype !== "Customer" || activeForm.doc.name !== message.customer) return;
		if (activeForm.is_dirty()) {
			frappe.show_alert({
				message: __("O endereço ou contato foi atualizado. Salve ou recarregue a ficha antes de continuar."),
				indicator: "orange",
			}, 8);
			return;
		}
		activeForm.reload_doc().then(() => {
			frappe.show_alert({
				message: __("Ficha atualizada com os novos dados de endereço ou contato."),
				indicator: "green",
			});
		});
	});
}

function sol_clone_customer_doc(doc) {
	if (doc === undefined) return undefined;
	return JSON.parse(JSON.stringify(doc));
}

function sol_customer_values_match(left, right) {
	return JSON.stringify(left ?? null) === JSON.stringify(right ?? null);
}

function sol_remember_customer_version(frm) {
	if (!frm.is_new() && !frm.is_dirty()) {
		frm.sol_last_server_doc = sol_clone_customer_doc(frm.doc);
	}
}

async function sol_merge_latest_customer_before_save(frm) {
	if (frm.is_new()) return;

	const timestamp = await frappe.db.get_value("Customer", frm.doc.name, "modified");
	const latest_modified = timestamp?.message?.modified;
	if (!latest_modified || latest_modified === frm.doc.modified) return;

	const response = await frappe.call({
		method: "frappe.client.get",
		args: { doctype: "Customer", name: frm.doc.name },
	});
	const latest = response.message;
	if (!latest) return;

	const baseline = frm.sol_last_server_doc || {};
	const local = sol_clone_customer_doc(frm.doc);
	const ignored = new Set([
		"doctype", "name", "creation", "modified", "modified_by", "owner",
		"docstatus", "idx", "__islocal", "__unsaved", "__onload",
	]);

	Object.keys(latest).forEach((fieldname) => {
		if (ignored.has(fieldname)) return;
		if (sol_customer_values_match(local[fieldname], baseline[fieldname])) {
			frm.doc[fieldname] = sol_clone_customer_doc(latest[fieldname]);
		}
	});
	frm.doc.modified = latest.modified;
	frm.doc.modified_by = latest.modified_by;
	frm.sol_last_server_doc = sol_clone_customer_doc(latest);
	frappe.show_alert({
		message: __("A ficha foi sincronizada com a versão mais recente antes de salvar."),
		indicator: "blue",
	});
}

function sol_money(value, currency = "BRL") {
	return format_currency(value || 0, currency);
}

function sol_new_customer_document(frm, doctype, defaults) {
	window.sol_customer_navigation?.start(frm.doc.name, doctype);
	if (doctype === "Issue") {
		frappe.model.with_doctype(doctype, () => {
			frappe.route_options = defaults;
			const name = frappe.model.make_new_doc_and_get_name(doctype, true);
			frappe.set_route("Form", doctype, name);
		});
		return;
	}
	frappe.new_doc(doctype, defaults);
}

function sol_new_customer_contract(frm) {
	frappe.call({
		method: "sol_brasil.subscription.get_customer_addresses",
		args: { customer: frm.doc.name },
		callback: ({ message }) => {
			const addresses = message || [];
			const open_contract = (address = null) => sol_new_customer_document(frm, "Subscription", {
				party_type: "Customer",
				party: frm.doc.name,
				custom_installation_address: address,
			});

			if (addresses.length <= 1) {
				open_contract(addresses[0]?.name || null);
				return;
			}
			frappe.prompt(
				[{
					fieldname: "address",
					fieldtype: "Select",
					label: __("Endereço de instalação"),
					options: addresses.map((row) => ({ label: row.label, value: row.name })),
					reqd: 1,
				}],
				(values) => open_contract(values.address),
				__("Selecione o endereço do contrato"),
				__("Continuar")
			);
		},
	});
}

function sol_add_internal_comment(frm) {
	frappe.prompt(
		[{
			fieldname: "content",
			fieldtype: "Small Text",
			label: __("Comentário interno"),
			description: __("Visível apenas para usuários internos com acesso a esta ficha."),
			reqd: 1,
		}],
		(values) => {
			frappe.call({
				method: "sol_brasil.customer.add_internal_comment",
				args: {
					reference_doctype: frm.doctype,
					reference_name: frm.doc.name,
					content: values.content,
				},
				freeze: true,
				freeze_message: __("Registrando no histórico..."),
				callback: () => {
					frappe.show_alert({ message: __("Comentário registrado no histórico interno."), indicator: "green" });
					frm.reload_doc();
				},
			});
		},
		__("Registrar comentário interno"),
		__("Registrar")
	);
}

function sol_change_customer_contract(frm) {
	frappe.call({
		method: "sol_brasil.customer_panel.get_available_contracts",
		args: { customer: frm.doc.name },
		callback: ({ message }) => {
			const contracts = message || [];
			if (!contracts.length) {
				frappe.msgprint({
					title: __("Nenhum contrato disponível"),
					message: __("Este cliente não possui contrato ativo disponível para vínculo."),
					indicator: "orange",
				});
				return;
			}
			const details = contracts.map((row) =>
				`<strong>${frappe.utils.escape_html(row.name)}</strong> — ${frappe.utils.escape_html(row.plans)} (${__(row.status)})`
			).join("<br>");
			frappe.prompt(
				[{
					fieldname: "contract",
					fieldtype: "Select",
					label: __("Contrato disponível"),
					options: contracts.map((row) => row.name).join("\n"),
					default: frm.doc.custom_linked_subscription,
					description: details,
					reqd: 1,
				}],
				(values) => {
					frm.set_value("custom_linked_subscription", values.contract).then(() => frm.save());
				},
				__("Consultar ou trocar contrato"),
				__("Vincular contrato")
			);
		},
	});
}

function sol_invoice_actions(invoice, allow_payment) {
	const name = frappe.utils.escape_html(invoice.name);
	return `
		<div class="btn-group btn-group-sm">
			<button class="btn btn-default sol-open-invoice" data-name="${name}">${__("Abrir")}</button>
			<button class="btn btn-default sol-print-invoice" data-name="${name}">${__("Imprimir")}</button>
			<button class="btn btn-default sol-download-invoice" data-name="${name}">${__("Baixar PDF")}</button>
			${allow_payment ? `<button class="btn btn-primary sol-pay-invoice" data-name="${name}">${__("Receber")}</button>` : ""}
		</div>`;
}

function sol_invoice_table(rows, allow_payment) {
	if (!rows.length) {
		return `<div class="text-muted py-4">${__("Nenhum boleto encontrado.")}</div>`;
	}
	return `<div class="table-responsive"><table class="table table-bordered">
		<thead><tr><th>${__("Boleto")}</th><th>${__("Emissão")}</th><th>${__("Vencimento")}</th><th>${__("Status")}</th><th>${__("Valor")}</th><th>${__("Em aberto")}</th><th>${__("Operações")}</th></tr></thead>
		<tbody>${rows.map((row) => `<tr>
			<td><a href="/desk/sales-invoice/${encodeURIComponent(row.name)}">${frappe.utils.escape_html(row.name)}</a></td>
			<td>${frappe.datetime.str_to_user(row.posting_date)}</td>
			<td>${frappe.datetime.str_to_user(row.due_date)}</td>
			<td>${__(row.status)}</td>
			<td>${sol_money(row.grand_total, row.currency)}</td>
			<td>${sol_money(row.outstanding_amount, row.currency)}</td>
			<td>${sol_invoice_actions(row, allow_payment)}</td>
		</tr>`).join("")}</tbody></table></div>`;
}

function sol_render_customer_panel(frm, data) {
	data = data || {};
	data.contracts = data.contracts || [];
	data.open_invoices = data.open_invoices || [];
	data.paid_invoices = data.paid_invoices || [];
	data.available_years = data.available_years || [new Date().getFullYear()];
	data.year = data.year || new Date().getFullYear();
	data.issues = data.issues || [];
	data.service_orders = data.service_orders || [];
	const contracts_wrapper = frm.fields_dict.custom_contracts_panel?.$wrapper;
	const financial_wrapper = frm.fields_dict.custom_financial_panel?.$wrapper;
	const service_wrapper = frm.fields_dict.custom_service_panel?.$wrapper;
	if (!contracts_wrapper || !financial_wrapper || !service_wrapper) return;

	contracts_wrapper.html(`
		<div class="d-flex justify-content-between align-items-center mb-3">
			<div><h4>${__("Contratos do cliente")}</h4><p class="text-muted">${__("Planos recorrentes e situação contratual.")}</p></div>
			<button class="btn btn-primary sol-new-contract">${__("Novo contrato")}</button>
		</div>
		<div class="table-responsive"><table class="table table-bordered">
			<thead><tr><th>${__("Contrato")}</th><th>${__("Plano")}</th><th>${__("Início")}</th><th>${__("Término")}</th><th>${__("Status")}</th><th>${__("Mensalidade")}</th></tr></thead>
			<tbody>${data.contracts.length ? data.contracts.map((row) => `<tr>
				<td><a href="/desk/subscription/${encodeURIComponent(row.name)}">${frappe.utils.escape_html(row.name)}</a></td>
				<td>${frappe.utils.escape_html(row.plans)}</td>
				<td>${frappe.datetime.str_to_user(row.start_date)}</td>
				<td>${row.end_date ? frappe.datetime.str_to_user(row.end_date) : "—"}</td>
				<td>${__(row.status)}</td><td>${sol_money(row.monthly_value)}</td>
			</tr>`).join("") : `<tr><td colspan="6" class="text-muted">${__("Nenhum contrato cadastrado.")}</td></tr>`}</tbody>
		</table></div>`);

	financial_wrapper.html(`
		<div class="d-flex justify-content-between align-items-center mb-3">
			<div><h4>${__("Boletos em aberto")}</h4><p class="text-muted">${__("Todos os títulos ainda pendentes deste cliente.")}</p></div>
			<button class="btn btn-primary sol-new-invoice">${__("Novo boleto")}</button>
		</div>
		${sol_invoice_table(data.open_invoices, true)}
		<div class="d-flex justify-content-between align-items-center mt-5 mb-3">
			<div><h4>${__("Boletos pagos")}</h4><p class="text-muted">${__("Histórico de títulos quitados no ano selecionado.")}</p></div>
			<select class="form-control sol-financial-year" style="width: 130px">${data.available_years.map((year) => `<option value="${year}" ${year === data.year ? "selected" : ""}>${year}</option>`).join("")}</select>
		</div>
		${sol_invoice_table(data.paid_invoices, false)}`);

	contracts_wrapper.find(".sol-new-contract").on("click", () => sol_new_customer_contract(frm));
	financial_wrapper.find(".sol-new-invoice").on("click", () => sol_new_customer_document(frm, "Sales Invoice", { customer: frm.doc.name }));
	financial_wrapper.find(".sol-financial-year").on("change", (event) => sol_load_customer_panel(frm, event.target.value));
	financial_wrapper.find(".sol-open-invoice").on("click", (event) => frappe.set_route("Form", "Sales Invoice", event.currentTarget.dataset.name));
	financial_wrapper.find(".sol-print-invoice").on("click", (event) => {
		window.open(`/printview?doctype=Sales%20Invoice&name=${encodeURIComponent(event.currentTarget.dataset.name)}&trigger_print=1&format=Standard&no_letterhead=0`, "_blank");
	});
	financial_wrapper.find(".sol-download-invoice").on("click", (event) => {
		window.open(`/api/method/frappe.utils.print_format.download_pdf?doctype=Sales%20Invoice&name=${encodeURIComponent(event.currentTarget.dataset.name)}&format=Standard&no_letterhead=0`, "_blank");
	});
	financial_wrapper.find(".sol-pay-invoice").on("click", (event) => {
		window.sol_customer_navigation?.start(frm.doc.name, "Payment Entry");
		frappe.call({
			method: "erpnext.accounts.doctype.payment_entry.payment_entry.get_payment_entry",
			args: { dt: "Sales Invoice", dn: event.currentTarget.dataset.name },
			callback: (response) => {
				const docs = frappe.model.sync(response.message);
				frappe.set_route("Form", docs[0].doctype, docs[0].name);
			},
		});
	});

	service_wrapper.html(`
		<div class="d-flex justify-content-between align-items-center mb-3">
			<div><h4>${__("Ordens de serviço")}</h4><p class="text-muted">${__("Visitas técnicas, instalações e manutenções vinculadas ao cliente.")}</p></div>
			<div class="btn-group"><button class="btn btn-default sol-new-issue">${__("Novo atendimento")}</button><button class="btn btn-primary sol-new-service-order">${__("Nova ordem de serviço")}</button></div>
		</div>
		<div class="table-responsive"><table class="table table-bordered">
			<thead><tr><th>${__("OS")}</th><th>${__("Data")}</th><th>${__("Horário")}</th><th>${__("Tipo")}</th><th>${__("Execução")}</th><th>${__("Situação")}</th><th>${__("Operações")}</th></tr></thead>
			<tbody>${data.service_orders.length ? data.service_orders.map((row) => `<tr>
				<td><a href="/desk/maintenance-visit/${encodeURIComponent(row.name)}">${frappe.utils.escape_html(row.name)}</a></td>
				<td>${frappe.datetime.str_to_user(row.mntc_date)}</td><td>${row.mntc_time || "—"}</td>
				<td>${__(row.maintenance_type || "Unscheduled")}</td><td>${__(row.completion_status || "Pendente")}</td><td>${__(row.status || "Draft")}</td>
				<td><button class="btn btn-sm btn-default sol-open-service-order" data-name="${frappe.utils.escape_html(row.name)}">${__("Abrir OS")}</button></td>
			</tr>`).join("") : `<tr><td colspan="7" class="text-muted">${__("Nenhuma ordem de serviço cadastrada.")}</td></tr>`}</tbody>
		</table></div>
		<h4 class="mt-5">${__("Atendimentos")}</h4><p class="text-muted">${__("Solicitações que podem ou não originar uma ordem de serviço.")}</p>
		<div class="table-responsive"><table class="table table-bordered">
			<thead><tr><th>${__("Atendimento")}</th><th>${__("Assunto")}</th><th>${__("Abertura")}</th><th>${__("Prioridade")}</th><th>${__("Status")}</th></tr></thead>
			<tbody>${data.issues.length ? data.issues.map((row) => `<tr>
				<td><a href="/desk/issue/${encodeURIComponent(row.name)}">${frappe.utils.escape_html(row.name)}</a></td><td>${frappe.utils.escape_html(row.subject)}</td>
				<td>${frappe.datetime.str_to_user(row.opening_date)}</td><td>${__(row.priority || "Medium")}</td><td>${__(row.status)}</td>
			</tr>`).join("") : `<tr><td colspan="5" class="text-muted">${__("Nenhum chamado cadastrado.")}</td></tr>`}</tbody>
		</table></div>`);
	service_wrapper.find(".sol-new-issue").on("click", () => sol_new_customer_document(frm, "Issue", { customer: frm.doc.name }));
	service_wrapper.find(".sol-new-service-order").on("click", () => sol_new_customer_document(frm, "Maintenance Visit", { customer: frm.doc.name }));
	service_wrapper.find(".sol-open-service-order").on("click", (event) => frappe.set_route("Form", "Maintenance Visit", event.currentTarget.dataset.name));
}

function sol_load_customer_panel(frm, year = null) {
	if (frm.is_new()) return;
	const contracts_wrapper = frm.fields_dict.custom_contracts_panel?.$wrapper;
	const financial_wrapper = frm.fields_dict.custom_financial_panel?.$wrapper;
	const service_wrapper = frm.fields_dict.custom_service_panel?.$wrapper;
	contracts_wrapper?.html(`<div class="text-muted py-4">${__("Carregando contratos...")}</div>`);
	financial_wrapper?.html(`<div class="text-muted py-4">${__("Carregando financeiro...")}</div>`);
	service_wrapper?.html(`<div class="text-muted py-4">${__("Carregando atendimentos...")}</div>`);
	frappe.call({
		method: "sol_brasil.customer_panel.get_customer_panel",
		args: { customer: frm.doc.name, year },
		callback: (response) => sol_render_customer_panel(frm, response.message),
		error: () => {
			contracts_wrapper?.html(`<div class="text-danger py-4">${__("Não foi possível carregar os contratos.")}</div>`);
			financial_wrapper?.html(`<div class="text-danger py-4">${__("Não foi possível carregar os boletos.")}</div>`);
			service_wrapper?.html(`<div class="text-danger py-4">${__("Não foi possível carregar os atendimentos.")}</div>`);
		},
	});
}

function sol_query_fiberhome_signal(frm) {
	frappe.call({
		method: "sol_brasil.fiberhome_tl1.query_signal",
		args: { customer: frm.doc.name },
		freeze: true,
		freeze_message: __("Consultando potência óptica no UNM..."),
	}).then(({ message }) => {
		frm.reload_doc();
		frappe.show_alert({
			message: __(`Sinal atualizado: RX ${message.rx_power} dBm / TX ${message.tx_power} dBm`),
			indicator: message.rx_status === "Normal" ? "green" : "orange",
		});
	});
}

function sol_authorize_fiberhome_onu(frm) {
	frappe.confirm(
		__("Autorizar esta ONU no UNM usando os dados ópticos cadastrados no cliente?"),
		() => frappe.call({
			method: "sol_brasil.fiberhome_tl1.authorize_onu",
			args: { customer: frm.doc.name },
			freeze: true,
			freeze_message: __("Autorizando ONU no UNM..."),
		}).then(() => frappe.show_alert({ message: __("ONU autorizada com sucesso."), indicator: "green" }))
	);
}

function sol_deauthorize_fiberhome_onu(frm) {
	const dialog = new frappe.ui.Dialog({
		title: __("Confirmar desautorização da ONU"),
		fields: [
			{ fieldtype: "HTML", options: `<div class="alert alert-danger">${__("Esta ação também pode remover os serviços associados à ONU. Para confirmar, digite exatamente o identificador do cliente:")} <b>${frappe.utils.escape_html(frm.doc.name)}</b></div>` },
			{ fieldname: "confirmation", fieldtype: "Data", label: __("Confirmação"), reqd: 1 },
		],
		primary_action_label: __("Desautorizar ONU"),
		primary_action(values) {
			dialog.hide();
			frappe.call({
				method: "sol_brasil.fiberhome_tl1.deauthorize_onu",
				args: { customer: frm.doc.name, confirmation: values.confirmation },
				freeze: true,
				freeze_message: __("Desautorizando ONU no UNM..."),
			}).then(() => frappe.show_alert({ message: __("ONU desautorizada."), indicator: "orange" }));
		},
	});
	dialog.show();
}

frappe.ui.form.on("Customer", {
	onload_post_render(frm) {
		sol_watch_customer_references(frm);
		sol_remember_customer_version(frm);
		setTimeout(() => sol_load_customer_panel(frm), 100);
		setTimeout(() => sol_reorder_customer_tabs(frm), 120);
	},

	refresh(frm) {
		sol_remember_customer_version(frm);
		frappe.breadcrumbs.set_doctype_module("Customer", "SOL Brasil");
		setTimeout(() => sol_set_customer_breadcrumb(frm), 0);
		setTimeout(() => sol_reorder_customer_tabs(frm), 100);
		sol_refresh_customer_tax_fields(frm);
		frm.toggle_display("sales_team_tab", false);
		frm.set_query("custom_linked_subscription", () => ({
			filters: {
				party_type: "Customer",
				party: frm.doc.name,
				status: ["not in", ["Cancelled", "Completed"]],
			},
		}));
		setTimeout(() => sol_load_customer_panel(frm), 250);
		$(frm.wrapper)
			.off("click.sol_customer_panels")
			.on(
				"click.sol_customer_panels",
				'[data-fieldname="custom_contracts_tab"], [data-fieldname="custom_financial_tab"], [data-fieldname="custom_service_tab"]',
				() => setTimeout(() => sol_load_customer_panel(frm), 50)
			);
		if (!frm.is_new()) {
			const roles = frappe.user_roles || [];
			const can_query_fiberhome = roles.some((role) => ["Consulta de Rede FiberHome", "Operação de Rede FiberHome", "Administração FiberHome", "System Manager"].includes(role));
			const can_operate_fiberhome = roles.some((role) => ["Operação de Rede FiberHome", "Administração FiberHome", "System Manager"].includes(role));
			if (can_query_fiberhome) {
				frm.add_custom_button(__("Consultar sinal da ONU"), () => sol_query_fiberhome_signal(frm), __("FiberHome"));
			}
			if (can_operate_fiberhome) {
				frm.add_custom_button(__("Autorizar ONU"), () => sol_authorize_fiberhome_onu(frm), __("FiberHome"));
				frm.add_custom_button(__("Desautorizar ONU"), () => sol_deauthorize_fiberhome_onu(frm), __("FiberHome"));
			}
			frm.add_custom_button(__("Registrar comentário interno"), () => {
				sol_add_internal_comment(frm);
			}, __("Operações do cliente"));
			frm.add_custom_button(__("Novo contrato"), () => {
				sol_new_customer_contract(frm);
			}, __("Operações do cliente"));
			frm.add_custom_button(__("Emitir fatura"), () => {
				sol_new_customer_document(frm, "Sales Invoice", { customer: frm.doc.name });
			}, __("Operações do cliente"));
			frm.add_custom_button(__("Novo atendimento"), () => {
				sol_new_customer_document(frm, "Issue", { customer: frm.doc.name });
			}, __("Operações do cliente"));
			frm.add_custom_button(__("Vincular equipamento"), () => {
				sol_new_customer_document(frm, "Asset", { customer: frm.doc.name });
			}, __("Operações do cliente"));
		}
	},

	timeline_refresh(frm) {
		sol_setup_customer_timeline_pagination(frm);
	},

	async before_save(frm) {
		frm.sol_customer_syncing = true;
		try {
			await sol_merge_latest_customer_before_save(frm);
		} finally {
			frm.sol_customer_syncing = false;
		}
	},

	after_save(frm) {
		sol_remember_customer_version(frm);
	},

	custom_change_contract(frm) {
		if (frm.is_new()) {
			frappe.msgprint(__("Salve o cliente antes de vincular um contrato."));
			return;
		}
		sol_change_customer_contract(frm);
	},

	custom_person_type(frm) {
		frm.set_value("customer_type", frm.doc.custom_person_type === "Pessoa Física" ? "Individual" : "Company");
		sol_refresh_customer_tax_fields(frm);
		if (frm.doc.custom_tax_document) {
			frm.trigger("custom_tax_document");
		}
	},

	customer_type(frm) {
		frm.set_value(
			"custom_person_type",
			frm.doc.customer_type === "Individual" ? "Pessoa Física" : "Pessoa Jurídica"
		);
		sol_refresh_customer_tax_fields(frm);
		if (frm.doc.custom_tax_document) {
			frm.trigger("custom_tax_document");
		}
	},

	tax_id(frm) {
		const formatted = sol_format_document(frm.doc.tax_id);
		if (formatted && formatted !== frm.doc.tax_id) {
			frm.set_value("tax_id", formatted);
		}
	},

	custom_tax_document(frm) {
		const formatted = sol_format_document(frm.doc.custom_tax_document);
		if (formatted && formatted !== frm.doc.custom_tax_document) {
			frm.set_value("custom_tax_document", formatted);
		}
		if (formatted !== frm.doc.tax_id) {
			frm.set_value("tax_id", formatted);
		}
	},
});
