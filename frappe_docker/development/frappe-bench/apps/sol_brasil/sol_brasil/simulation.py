import random

import frappe
from frappe.utils import add_days, getdate, today

from sol_brasil.customer import format_cpf_cnpj
from sol_brasil.demo import DEMO_ITEM, DEMO_PLAN, _create_item, _create_plan


SIMULATION_OLT = "OLT-SIMULACAO-01"
SIMULATION_PREFIX = "SIM-ISP-"
FIRST_NAMES = [
	"Ana", "Bruno", "Carla", "Daniel", "Elisa", "Fabio", "Gabriela", "Henrique",
	"Isabela", "Joao", "Karen", "Lucas", "Mariana", "Nicolas", "Olivia", "Paulo",
	"Renata", "Samuel", "Tatiana", "Vinicius",
]
LAST_NAMES = [
	"Almeida", "Barbosa", "Cardoso", "Dias", "Esteves", "Ferreira", "Gomes", "Lima",
	"Martins", "Nascimento", "Oliveira", "Pereira", "Queiroz", "Rocha", "Santos", "Silva",
	"Teixeira", "Vieira", "Xavier", "Araujo",
]
CITIES = [
	("Quatipuru", "Pará"), ("Pirabas", "Pará"), ("Salinópolis", "Pará"),
	("Primavera", "Pará"), ("Capanema", "Pará"),
]


def _company():
	name = frappe.db.get_value("Company", {"name": ["like", "%Demo%"]}, "name")
	name = name or frappe.db.get_single_value("Global Defaults", "default_company")
	name = name or frappe.db.get_value("Company", {}, "name")
	if not name:
		frappe.throw("Cadastre uma empresa antes de executar a simulação.")
	return frappe.get_cached_doc("Company", name)


def _cpf(index):
	base = f"{700000000 + index:09d}"
	numbers = [int(value) for value in base]
	for size in (9, 10):
		total = sum(numbers[position] * (size + 1 - position) for position in range(size))
		numbers.append((total * 10 % 11) % 10)
	return format_cpf_cnpj("".join(str(value) for value in numbers))


def _create_network():
	if not frappe.db.exists("OLT", SIMULATION_OLT):
		frappe.get_doc({
			"doctype": "OLT",
			"identificacao": SIMULATION_OLT,
			"situacao": "Ativa",
			"quantidade_slots_pon": 4,
			"pons_por_slot": 16,
			"observacoes": "Estrutura fictícia criada pela simulação de 200 clientes.",
		}).insert(ignore_permissions=True)

	ctos = []
	for slot in range(1, 5):
		for pon in range(1, 17):
			name = f"CTO-SIM-S{slot:02d}-P{pon:02d}"
			if not frappe.db.exists("Caixa de Atendimento", name):
				frappe.get_doc({
					"doctype": "Caixa de Atendimento",
					"identificacao": name,
					"situacao": "Ativa",
					"capacidade": 8,
					"olt": SIMULATION_OLT,
					"slot": str(slot),
					"pon": str(pon),
					"endereco_referencia": f"Rede simulada — setor {slot}, rota {pon}",
				}).insert(ignore_permissions=True)
			ctos.append({"name": name, "slot": slot, "pon": pon})
	return ctos


def _create_customer(index, group, territory, status):
	cpf = _cpf(index)
	existing = frappe.db.get_value("Customer", {"tax_id": cpf}, "name")
	if existing:
		return frappe.get_doc("Customer", existing)

	first = FIRST_NAMES[(index - 1) % len(FIRST_NAMES)]
	last = LAST_NAMES[((index - 1) // len(FIRST_NAMES)) % len(LAST_NAMES)]
	doc = frappe.get_doc({
		"doctype": "Customer",
		"customer_name": f"{first} {last}",
		"customer_type": "Individual",
		"customer_group": group,
		"territory": territory,
		"custom_tax_document": cpf,
		"mobile_no": f"(91) 98{index:07d}"[-15:],
		"custom_connection_status": status,
		"custom_subscription_plan": DEMO_PLAN,
		"disabled": 0,
	})
	doc.insert(ignore_permissions=True)
	return doc


def _create_address(customer, index):
	existing = frappe.db.get_value(
		"Dynamic Link",
		{"parenttype": "Address", "link_doctype": "Customer", "link_name": customer.name},
		"parent",
	)
	if existing:
		return existing
	city, state = CITIES[(index - 1) % len(CITIES)]
	address = frappe.get_doc({
		"doctype": "Address",
		"address_title": f"Instalação {customer.customer_name}",
		"address_type": "Other",
		"address_line1": f"Rua da Simulação, {100 + index}",
		"address_line2": f"Bairro Teste {(index % 12) + 1}",
		"city": city,
		"state": state,
		"country": "Brazil",
		"pincode": f"687{index % 100:02d}-000",
		"is_primary_address": 1,
		"links": [{"link_doctype": "Customer", "link_name": customer.name}],
	})
	address.insert(ignore_permissions=True)
	return address.name


def _create_subscription(company, customer, address, index, status, cto):
	existing = frappe.db.get_value(
		"Subscription",
		{"party_type": "Customer", "party": customer.name, "custom_pppoe_username": f"sim{index:04d}"},
		"name",
	)
	if existing:
		return frappe.get_doc("Subscription", existing)

	doc = frappe.get_doc({
		"doctype": "Subscription",
		"party_type": "Customer",
		"party": customer.name,
		"company": company.name,
		"start_date": getdate(today()),
		"generate_invoice_at": "End of the current subscription period",
		"submit_invoice": 0,
		"cost_center": company.cost_center,
		"custom_installation_address": address,
		"custom_pppoe_username": f"sim{index:04d}",
		"custom_pppoe_password": f"Sim@{index:04d}",
		"custom_connection_status": status,
		"custom_activation_date": add_days(getdate(today()), -(index % 330)),
		"custom_ipv4_address": f"100.65.{(index - 1) // 254}.{((index - 1) % 254) + 1}",
		"custom_mac_address": f"02:10:{(index >> 16) & 255:02X}:{(index >> 8) & 255:02X}:{index & 255:02X}:{index % 251:02X}",
		"custom_olt": SIMULATION_OLT,
		"custom_olt_slot_select": str(cto["slot"]),
		"custom_pon_select": str(cto["pon"]),
		"custom_installation_box_link": cto["name"],
		"custom_cto_port": str(((index - 1) % 8) + 1),
		"plans": [{"plan": DEMO_PLAN, "qty": 1}],
	})
	doc.insert(ignore_permissions=True)
	frappe.db.set_value("Customer", customer.name, "custom_linked_subscription", doc.name, update_modified=False)
	return doc


def _create_invoice(company, customer, subscription, index):
	reference = f"{SIMULATION_PREFIX}FAT-{index:04d}"
	existing = frappe.db.get_value(
		"Sales Invoice", {"po_no": reference, "docstatus": ["<", 2]}, "name"
	)
	if existing:
		_set_simulation_due_date(existing, index)
		return frappe.get_doc("Sales Invoice", existing)

	paid = index % 4 == 0
	posting_date, due_date = _simulation_dates(index)
	rate = [79.90, 99.90, 109.90, 129.90][index % 4]
	doc = frappe.get_doc({
		"doctype": "Sales Invoice",
		"company": company.name,
		"customer": customer.name,
		"subscription": subscription.name,
		"posting_date": posting_date,
		"set_posting_time": 1,
		"due_date": due_date,
		"po_no": reference,
		"currency": company.default_currency,
		"debit_to": company.default_receivable_account,
		"remarks": "DADO FICTÍCIO — MASSA DE SIMULAÇÃO SOL PROVEDOR",
		"items": [{
			"item_code": DEMO_ITEM,
			"qty": 1,
			"rate": rate,
			"income_account": company.default_income_account,
			"cost_center": company.cost_center,
		}],
	})
	doc.insert(ignore_permissions=True)
	doc.submit()
	if paid:
		from erpnext.accounts.doctype.payment_entry.payment_entry import get_payment_entry

		payment = get_payment_entry("Sales Invoice", doc.name)
		payment.reference_no = f"{SIMULATION_PREFIX}PAG-{index:04d}"
		payment.reference_date = due_date
		payment.remarks = "PAGAMENTO FICTÍCIO — MASSA DE SIMULAÇÃO"
		payment.insert(ignore_permissions=True)
		payment.submit()
	return doc


def _simulation_dates(index):
	paid = index % 4 == 0
	if index % 7 == 0 and not paid:
		return add_days(getdate(today()), -30), add_days(getdate(today()), -20)
	if index % 5 == 0 and not paid:
		return add_days(getdate(today()), -15), add_days(getdate(today()), -7)
	return add_days(getdate(today()), -10), add_days(getdate(today()), 10)


def _set_simulation_due_date(invoice, index):
	posting_date, due_date = _simulation_dates(index)
	frappe.db.set_value(
		"Sales Invoice", invoice, {"posting_date": posting_date, "due_date": due_date}, update_modified=False
	)


def _create_issue(company, customer, index):
	if index % 10:
		return
	subject_name = frappe.db.get_value("Assunto de Atendimento", {"ativo": 1}, "name")
	if not subject_name:
		return
	subject = f"{SIMULATION_PREFIX}Atendimento {index:04d}"
	if frappe.db.exists("Issue", {"customer": customer.name, "subject": subject}):
		return
	frappe.get_doc({
		"doctype": "Issue",
		"subject": subject,
		"customer": customer.name,
		"company": company.name,
		"priority": ["Low", "Medium", "High"][index % 3],
		"custom_service_subject": subject_name,
		"description": "Atendimento fictício para teste de volume e navegação.",
	}).insert(ignore_permissions=True)


@frappe.whitelist()
def populate_realistic_demo(count=200, seed=20260826):
	count = max(200, min(int(count), 512))
	random.seed(int(seed))
	company = _company()
	_create_item()
	_create_plan(company)
	ctos = _create_network()
	group = frappe.db.get_value("Customer Group", {"is_group": 0}, "name")
	territory = frappe.db.get_value("Territory", {"is_group": 0}, "name")
	if not group or not territory:
		frappe.throw("Cadastre ao menos um grupo de clientes e um território folha.")

	stats = {"customers": 0, "subscriptions": 0, "invoices": 0, "ctos": len(ctos)}
	for index in range(1, count + 1):
		status = "Aguardando instalação"
		customer = _create_customer(index, group, territory, status)
		address = _create_address(customer, index)
		cto = ctos[(index - 1) // 8]
		subscription = _create_subscription(company, customer, address, index, status, cto)
		_create_invoice(company, customer, subscription, index)
		_create_issue(company, customer, index)
		stats["customers"] += 1
		stats["subscriptions"] += 1
		stats["invoices"] += 1
		if index % 10 == 0:
			frappe.db.commit()
			print(f"Simulação: {index}/{count} clientes processados")

	from sol_brasil.business_rules import cancel_contract, recalculate_all_contract_statuses

	# Limpa somente estados da massa identificada, para que execuções antigas não
	# preservem cancelamentos que antes eram distribuídos aleatoriamente.
	frappe.db.sql(
		"""
		UPDATE `tabSubscription`
		SET custom_connection_status = 'Aguardando instalação'
		WHERE custom_pppoe_username LIKE 'sim%%'
		"""
	)
	recalculate_all_contract_statuses()
	for index in range(20, count + 1, 20):
		subscription = frappe.db.get_value(
			"Subscription", {"custom_pppoe_username": f"sim{index:04d}"}, "name"
		)
		if subscription:
			cancel_contract(subscription)
	frappe.db.commit()
	stats["olt"] = SIMULATION_OLT
	stats["paid_invoices"] = count // 4
	stats["issues"] = count // 10
	return stats
