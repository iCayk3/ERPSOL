import frappe
from frappe import _
from frappe.utils import fmt_money, get_link_to_form


INVOICE_FIELDS = {
	"posting_date": "Data de emissão",
	"due_date": "Vencimento",
	"grand_total": "Valor total",
	"outstanding_amount": "Valor em aberto",
	"status": "Situação",
}


def _money(value, currency):
	return fmt_money(value or 0, currency=currency or "BRL")


def _customer_exists(customer):
	return customer and frappe.db.exists("Customer", customer)


def _add_activity(customer, text):
	if _customer_exists(customer):
		frappe.get_doc("Customer", customer).add_comment("Comment", text=text)


def _invoice_link(doc):
	return get_link_to_form("Sales Invoice", doc.name, doc.name)


def register_invoice_creation(doc, method=None):
	if not _customer_exists(doc.customer):
		return
	_add_activity(
		doc.customer,
		_("Fatura/boleto {0} criado no valor de {1}, com vencimento em {2}.").format(
			_invoice_link(doc), _money(doc.grand_total, doc.currency), doc.due_date or "não definido"
		),
	)


def register_invoice_update(doc, method=None):
	previous = doc.get_doc_before_save()
	if not previous or doc.docstatus != 0 or not _customer_exists(doc.customer):
		return
	changes = []
	for fieldname, label in INVOICE_FIELDS.items():
		old_value = previous.get(fieldname)
		new_value = doc.get(fieldname)
		if old_value == new_value:
			continue
		if fieldname in ("grand_total", "outstanding_amount"):
			old_value = _money(old_value, doc.currency)
			new_value = _money(new_value, doc.currency)
		changes.append(_('{0}: de "{1}" para "{2}"').format(label, old_value or "vazio", new_value or "vazio"))
	if changes:
		_add_activity(
			doc.customer,
			_("Fatura/boleto {0} alterado: {1}.").format(_invoice_link(doc), "; ".join(changes)),
		)


def register_invoice_submit(doc, method=None):
	_add_activity(
		doc.customer,
		_("Fatura/boleto {0} emitido no valor de {1}. Valor em aberto: {2}.").format(
			_invoice_link(doc),
			_money(doc.grand_total, doc.currency),
			_money(doc.outstanding_amount, doc.currency),
		),
	)


def register_invoice_cancel(doc, method=None):
	_add_activity(
		doc.customer,
		_("Fatura/boleto {0} cancelado. Valor: {1}.").format(
			_invoice_link(doc), _money(doc.grand_total, doc.currency)
		),
	)


def register_invoice_deletion(doc, method=None):
	_add_activity(
		doc.customer,
		_("Fatura/boleto {0} excluído da ficha do cliente.").format(frappe.bold(doc.name)),
	)


def _payment_customer(doc):
	return doc.party if doc.party_type == "Customer" else None


def _payment_references(doc):
	links = []
	for row in doc.get("references") or []:
		if row.reference_doctype and row.reference_name:
			links.append(get_link_to_form(row.reference_doctype, row.reference_name, row.reference_name))
	return ", ".join(links) or "sem documento vinculado"


def register_payment_creation(doc, method=None):
	customer = _payment_customer(doc)
	if not customer:
		return
	_add_activity(
		customer,
		_("Recebimento {0} criado no valor de {1}; referências: {2}.").format(
			get_link_to_form("Payment Entry", doc.name, doc.name),
			_money(doc.paid_amount, doc.paid_from_account_currency or doc.paid_to_account_currency),
			_payment_references(doc),
		),
	)


def register_payment_submit(doc, method=None):
	customer = _payment_customer(doc)
	if not customer:
		return
	_add_activity(
		customer,
		_("Pagamento confirmado em {0}: {1}. Referências: {2}.").format(
			get_link_to_form("Payment Entry", doc.name, doc.name),
			_money(doc.paid_amount, doc.paid_from_account_currency or doc.paid_to_account_currency),
			_payment_references(doc),
		),
	)


def register_payment_cancel(doc, method=None):
	customer = _payment_customer(doc)
	if customer:
		_add_activity(
			customer,
			_("Pagamento {0} estornado/cancelado no valor de {1}.").format(
				get_link_to_form("Payment Entry", doc.name, doc.name),
				_money(doc.paid_amount, doc.paid_from_account_currency or doc.paid_to_account_currency),
			),
		)


def register_payment_deletion(doc, method=None):
	customer = _payment_customer(doc)
	if customer:
		_add_activity(
			customer,
			_("Recebimento {0} excluído da ficha do cliente.").format(frappe.bold(doc.name)),
		)
