import re

import frappe
from frappe import _


def digits(value: str | None) -> str:
	return re.sub(r"\D", "", value or "")


def is_valid_cpf(value: str | None) -> bool:
	number = digits(value)
	if len(number) != 11 or len(set(number)) == 1:
		return False

	for size in (9, 10):
		total = sum(int(number[index]) * (size + 1 - index) for index in range(size))
		check_digit = (total * 10 % 11) % 10
		if check_digit != int(number[size]):
			return False
	return True


def is_valid_cnpj(value: str | None) -> bool:
	number = digits(value)
	if len(number) != 14 or len(set(number)) == 1:
		return False

	for size, weights in (
		(12, (5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2)),
		(13, (6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2)),
	):
		total = sum(int(number[index]) * weights[index] for index in range(size))
		remainder = total % 11
		check_digit = 0 if remainder < 2 else 11 - remainder
		if check_digit != int(number[size]):
			return False
	return True


def format_cpf_cnpj(value: str | None) -> str:
	number = digits(value)
	if len(number) == 11:
		return f"{number[:3]}.{number[3:6]}.{number[6:9]}-{number[9:]}"
	if len(number) == 14:
		return f"{number[:2]}.{number[2:5]}.{number[5:8]}/{number[8:12]}-{number[12:]}"
	return value or ""


def validate_customer(doc, method=None):
	doc.custom_person_type = "Pessoa Física" if doc.customer_type == "Individual" else "Pessoa Jurídica"
	document = digits(doc.get("custom_tax_document") or doc.tax_id)

	if not document:
		frappe.throw(_("Informe o CPF ou CNPJ do cliente."), title=_("Documento obrigatório"))

	if doc.customer_type == "Individual":
		if not is_valid_cpf(document):
			frappe.throw(_("O CPF informado é inválido."), title=_("CPF inválido"))
	elif not is_valid_cnpj(document):
		frappe.throw(_("O CNPJ informado é inválido."), title=_("CNPJ inválido"))

	doc.tax_id = format_cpf_cnpj(document)
	doc.custom_tax_document = doc.tax_id
	existing = frappe.db.get_value(
		"Customer",
		{"tax_id": doc.tax_id, "name": ("!=", doc.name or "")},
		"name",
	)
	if existing:
		frappe.throw(
			_("O documento {0} já está cadastrado no cliente {1}.").format(doc.tax_id, existing),
			title=_("CPF/CNPJ duplicado"),
		)

	if doc.get("custom_linked_subscription"):
		contract = frappe.db.get_value(
			"Subscription",
			doc.custom_linked_subscription,
			["party_type", "party", "status"],
			as_dict=True,
		)
		if not contract or contract.party_type != "Customer" or contract.party != doc.name:
			frappe.throw(
				_("O contrato selecionado não pertence a este cliente."),
				title=_("Contrato inválido"),
			)
		if contract.status in ("Cancelled", "Completed"):
			frappe.throw(
				_("Selecione um contrato ativo ou disponível para este cliente."),
				title=_("Contrato indisponível"),
			)
		plan = frappe.db.get_value(
			"Subscription Plan Detail",
			{"parent": doc.custom_linked_subscription, "parenttype": "Subscription"},
			"plan",
			order_by="idx asc",
		)
		if plan:
			doc.custom_subscription_plan = plan


def validate_lead(doc, method=None):
	if not (doc.first_name or doc.lead_name or doc.company_name):
		frappe.throw(_("Informe o nome do futuro cliente."), title=_("Nome obrigatório"))
	if not (doc.mobile_no or doc.phone or doc.email_id):
		frappe.throw(
			_("Informe pelo menos um telefone ou e-mail para contato."),
			title=_("Contato obrigatório"),
		)

@frappe.whitelist()
def add_internal_comment(reference_doctype, reference_name, content):
	if reference_doctype not in ("Customer", "Lead"):
		frappe.throw("O histórico interno está disponível somente para clientes e Leads.")
	doc = frappe.get_doc(reference_doctype, reference_name)
	doc.check_permission("read")
	text = (content or "").strip()
	if not text:
		frappe.throw("Digite o comentário que deseja registrar.")
	comment = doc.add_comment("Comment", text=text)
	return {"name": comment.name, "creation": comment.creation}
