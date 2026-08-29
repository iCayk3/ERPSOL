frappe.pages["central-de-cobranca"].on_page_load = function (wrapper) {
	const page = frappe.ui.make_app_page({
		parent: wrapper,
		title: __("Central de Cobrança"),
		single_column: true,
	});

	const state = {
		period: "overdue",
		reference_month: "",
		connection_status: "",
		limit: 100,
	};

	page.add_inner_button(__("Recalcular contratos"), () => {
		frappe.call({
			method: "sol_brasil.central_cobranca.recalculate_contracts",
			freeze: true,
			freeze_message: __("Recalculando contratos..."),
			callback: () => load(),
		});
	});
	page.add_inner_button(__("Relatório mensal"), () => show_report());

	$(`
		<style>
			.sol-collection-center { padding: 16px 0 32px; }
			.sol-collection-toolbar { display: flex; gap: 12px; align-items: end; flex-wrap: wrap; margin-bottom: 16px; }
			.sol-collection-toolbar .form-group { margin-bottom: 0; min-width: 180px; }
			.sol-collection-metrics { display: grid; grid-template-columns: repeat(auto-fit, minmax(170px, 1fr)); gap: 12px; margin-bottom: 16px; }
			.sol-collection-metric { border: 1px solid var(--border-color); border-radius: 8px; padding: 12px; background: var(--card-bg); }
			.sol-collection-metric .label { color: var(--text-muted); font-size: 12px; margin-bottom: 6px; }
			.sol-collection-metric .value { font-size: 20px; font-weight: 650; line-height: 1.2; }
			.sol-collection-status { display: flex; gap: 8px; flex-wrap: wrap; margin-bottom: 16px; }
			.sol-collection-status .pill { border: 1px solid var(--border-color); border-radius: 999px; padding: 5px 10px; background: var(--fg-color); color: var(--text-muted); }
			.sol-collection-table th { white-space: nowrap; }
			.sol-collection-table td { vertical-align: middle !important; }
			.sol-collection-actions { display: flex; gap: 6px; flex-wrap: wrap; }
			.sol-overdue-days { font-weight: 650; color: var(--red-600); }
		</style>
		<div class="sol-collection-center">
			<div class="sol-collection-toolbar">
				<div class="form-group">
					<label>${__("Mês de referência")}</label>
					<select class="form-control sol-filter-reference-month"></select>
				</div>
				<div class="form-group">
					<label>${__("Período")}</label>
					<select class="form-control sol-filter-period">
						<option value="overdue">${__("Vencidas")}</option>
						<option value="today">${__("Vencem hoje")}</option>
						<option value="upcoming">${__("A vencer")}</option>
						<option value="all">${__("Todas em aberto")}</option>
					</select>
				</div>
				<div class="form-group">
					<label>${__("Status do contrato")}</label>
					<select class="form-control sol-filter-status">
						<option value="">${__("Todos")}</option>
						<option value="Ativo">${__("Ativo")}</option>
						<option value="Bloqueado">${__("Bloqueado")}</option>
						<option value="Suspenso">${__("Suspenso")}</option>
						<option value="Aguardando instalação">${__("Aguardando instalação")}</option>
						<option value="Cancelado">${__("Cancelado")}</option>
					</select>
				</div>
				<div class="form-group">
					<label>${__("Limite")}</label>
					<select class="form-control sol-filter-limit">
						<option value="50">50</option>
						<option value="100" selected>100</option>
						<option value="200">200</option>
						<option value="500">500</option>
					</select>
				</div>
				<button class="btn btn-primary sol-refresh">${__("Atualizar")}</button>
			</div>
			<div class="sol-collection-metrics"></div>
			<div class="sol-collection-status"></div>
			<div class="sol-collection-list"></div>
		</div>
	`).appendTo(page.body);

	const root = $(page.body);
	root.find(".sol-filter-reference-month").on("change", (event) => {
		state.reference_month = event.target.value;
		load();
	});
	root.find(".sol-filter-period").on("change", (event) => {
		state.period = event.target.value;
		load();
	});
	root.find(".sol-filter-status").on("change", (event) => {
		state.connection_status = event.target.value;
		load();
	});
	root.find(".sol-filter-limit").on("change", (event) => {
		state.limit = parseInt(event.target.value, 10) || 100;
		load();
	});
	root.find(".sol-refresh").on("click", () => load());

	function money(value, currency) {
		return format_currency(value || 0, currency || frappe.defaults.get_default("currency"));
	}

	function metric(label, value) {
		return `<div class="sol-collection-metric"><div class="label">${label}</div><div class="value">${value}</div></div>`;
	}

	function render(data) {
		const summary = data.summary || {};
		render_months(data.available_months || {});
		const currency = (data.rows && data.rows[0] && data.rows[0].currency) || frappe.defaults.get_default("currency");
		root.find(".sol-collection-metrics").html([
			metric(__("Em aberto"), `${summary.open_count || 0}<br>${money(summary.open_amount, currency)}`),
			metric(__("A cobrar"), `${summary.renegotiated_count || 0} ${__("reneg.")}<br>${money(summary.collection_amount, currency)}`),
			metric(__("Vencidas"), `${summary.overdue_count || 0}<br>${money(summary.overdue_amount, currency)}`),
			metric(__("Vencem hoje"), `${summary.due_today_count || 0}<br>${money(summary.due_today_amount, currency)}`),
		].join(""));
		root.find(".sol-collection-status").html((summary.by_status || []).map((row) => (
			`<span class="pill">${__(row.status)}: <b>${row.total}</b></span>`
		)).join(""));
		render_rows(data.rows || []);
	}

	function render_months(data) {
		const months = data.months || [];
		if (!state.reference_month) {
			state.reference_month = data.default_month || frappe.datetime.get_today().slice(0, 7);
		}
		root.find(".sol-filter-reference-month").html(months.map((row) => (
			`<option value="${frappe.utils.escape_html(row.value)}" ${row.value === state.reference_month ? "selected" : ""}>${frappe.utils.escape_html(row.value)} (${row.total})</option>`
		)).join("") || `<option value="${state.reference_month}">${state.reference_month}</option>`);
	}

	function render_rows(rows) {
		if (!rows.length) {
			root.find(".sol-collection-list").html(`<div class="text-muted py-5">${__("Nenhuma fatura encontrada para os filtros atuais.")}</div>`);
			return;
		}
		root.find(".sol-collection-list").html(`
			<div class="table-responsive">
				<table class="table table-bordered sol-collection-table">
					<thead>
						<tr>
							<th>${__("Cliente")}</th>
							<th>${__("Fatura")}</th>
							<th>${__("Referência")}</th>
							<th>${__("Vencimento")}</th>
							<th>${__("Atraso")}</th>
							<th>${__("Contrato")}</th>
							<th>${__("Status")}</th>
							<th>${__("Em aberto")}</th>
							<th>${__("A cobrar")}</th>
							<th>${__("Ações")}</th>
						</tr>
					</thead>
					<tbody>
						${rows.map((row) => `
							<tr>
								<td>
									<a href="/app/customer/${encodeURIComponent(row.customer)}">${frappe.utils.escape_html(row.customer_name || row.customer)}</a>
									<div class="text-muted small">${frappe.utils.escape_html(row.mobile_no || "")}</div>
								</td>
								<td><a href="/app/sales-invoice/${encodeURIComponent(row.name)}">${frappe.utils.escape_html(row.name)}</a></td>
								<td>
									${frappe.utils.escape_html(row.custom_billing_reference_month || "")}
									${row.custom_renegotiated ? `<div class="text-muted small">${__("Renegociado")}</div>` : ""}
								</td>
								<td>${frappe.datetime.str_to_user(row.due_date)}</td>
								<td>${row.overdue_days ? `<span class="sol-overdue-days">${row.overdue_days}d</span>` : __("No prazo")}</td>
								<td>
									${row.subscription ? `<a href="/app/subscription/${encodeURIComponent(row.subscription)}">${frappe.utils.escape_html(row.subscription)}</a>` : "—"}
									<div class="text-muted small">${frappe.utils.escape_html(row.custom_pppoe_username || row.custom_internet_plan || "")}</div>
								</td>
								<td>${__(row.custom_connection_status || "Sem contrato")}</td>
								<td>${money(row.outstanding_amount, row.currency)}</td>
								<td>
									${money(row.collection_amount, row.currency)}
									${row.custom_waive_interest_penalty ? `<div class="text-muted small">${__("Juros/multa zerados")}</div>` : ""}
								</td>
								<td>
									<div class="sol-collection-actions">
										<button class="btn btn-xs btn-default sol-open-customer" data-name="${frappe.utils.escape_html(row.customer)}">${__("Cliente")}</button>
										<button class="btn btn-xs btn-default sol-open-invoice" data-name="${frappe.utils.escape_html(row.name)}">${__("Fatura")}</button>
										<button
											class="btn btn-xs btn-default sol-renegotiate-invoice"
											data-name="${frappe.utils.escape_html(row.name)}"
											data-due-date="${frappe.utils.escape_html(row.due_date)}"
											data-amount="${frappe.utils.escape_html(row.custom_negotiated_amount || row.outstanding_amount || 0)}"
											data-waive="${frappe.utils.escape_html(row.custom_waive_interest_penalty || 0)}"
										>${__("Renegociar")}</button>
										<button class="btn btn-xs btn-primary sol-pay-invoice" data-name="${frappe.utils.escape_html(row.name)}">${__("Receber")}</button>
									</div>
								</td>
							</tr>
						`).join("")}
					</tbody>
				</table>
			</div>
		`);
		root.find(".sol-open-customer").on("click", (event) => frappe.set_route("Form", "Customer", event.currentTarget.dataset.name));
		root.find(".sol-open-invoice").on("click", (event) => frappe.set_route("Form", "Sales Invoice", event.currentTarget.dataset.name));
		root.find(".sol-renegotiate-invoice").on("click", (event) => renegotiate(
			event.currentTarget.dataset.name,
			event.currentTarget.dataset.dueDate,
			event.currentTarget.dataset.amount,
			event.currentTarget.dataset.waive
		));
		root.find(".sol-pay-invoice").on("click", (event) => {
			frappe.call({
				method: "erpnext.accounts.doctype.payment_entry.payment_entry.get_payment_entry",
				args: { dt: "Sales Invoice", dn: event.currentTarget.dataset.name },
				callback: (response) => {
					const docs = frappe.model.sync(response.message);
					frappe.set_route("Form", docs[0].doctype, docs[0].name);
				},
			});
		});
	}

	function renegotiate(invoice, current_due_date, current_amount, waive_interest_penalty) {
		const dialog = new frappe.ui.Dialog({
			title: __("Renegociar fatura"),
			fields: [
				{ fieldname: "new_due_date", fieldtype: "Date", label: __("Novo vencimento"), default: current_due_date, reqd: 1 },
				{ fieldname: "waive_interest_penalty", fieldtype: "Check", label: __("Zerar juros e multa"), default: parseInt(waive_interest_penalty, 10) || 0 },
				{ fieldname: "negotiated_amount", fieldtype: "Currency", label: __("Valor negociado"), default: parseFloat(current_amount) || 0, reqd: 1 },
				{ fieldname: "notes", fieldtype: "Small Text", label: __("Observações") },
			],
			primary_action_label: __("Renegociar"),
			primary_action(values) {
				frappe.call({
					method: "sol_brasil.central_cobranca.renegotiate_invoice",
					args: {
						invoice,
						new_due_date: values.new_due_date,
						negotiated_amount: values.negotiated_amount,
						waive_interest_penalty: values.waive_interest_penalty,
						notes: values.notes,
					},
					freeze: true,
					freeze_message: __("Registrando renegociação..."),
					callback: () => {
						dialog.hide();
						load();
					},
				});
			},
		});
		dialog.show();
	}

	function show_report() {
		frappe.call({
			method: "sol_brasil.central_cobranca.get_billing_report",
			args: { reference_month: state.reference_month },
			callback: ({ message }) => {
				const currency = frappe.defaults.get_default("currency");
				frappe.msgprint({
					title: __("Relatório mensal"),
					message: `
						<div class="table-responsive">
							<table class="table table-bordered">
								<tbody>
									<tr><th>${__("Mês de referência")}</th><td>${frappe.utils.escape_html(message.reference_month)}</td></tr>
									<tr><th>${__("Faturas")}</th><td>${message.invoices || 0}</td></tr>
									<tr><th>${__("Faturado")}</th><td>${money(message.billed, currency)}</td></tr>
									<tr><th>${__("Recebido")}</th><td>${money(message.received, currency)}</td></tr>
									<tr><th>${__("Em aberto")}</th><td>${money(message.open_amount, currency)}</td></tr>
									<tr><th>${__("A cobrar negociado")}</th><td>${money(message.collection_amount, currency)}</td></tr>
									<tr><th>${__("Renegociadas")}</th><td>${message.renegotiated_count || 0}</td></tr>
								</tbody>
							</table>
						</div>`,
					wide: true,
				});
			},
		});
	}

	function load() {
		root.find(".sol-collection-list").html(`<div class="text-muted py-5">${__("Carregando cobranças...")}</div>`);
		frappe.call({
			method: "sol_brasil.central_cobranca.get_collection_center",
			args: state,
			callback: (response) => render(response.message || {}),
		});
	}

	load();
};
