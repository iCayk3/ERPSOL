import json
import unittest
import uuid
from unittest.mock import patch

import frappe
from frappe.tests import IntegrationTestCase

from sol_brasil.radius_provisioning import _reply_attributes, create_provisioning_event
from sol_brasil.internet_plan import validate_internet_plan
from sol_brasil.subscription import _validate_pppoe_and_network


class TestRadiusModels(IntegrationTestCase):
	def test_contract_owns_and_normalizes_its_pppoe(self):
		contract = frappe._dict(
			custom_pppoe_username=" Ponto.Empresa ",
			custom_pppoe_password="senha",
			custom_ipv4_address="100.64.10.20",
			custom_mac_address="aa-bb-cc-dd-ee-ff",
			custom_vlan_id=100,
			custom_onu_number=10,
		)
		_validate_pppoe_and_network(contract)
		self.assertEqual(contract.custom_pppoe_username, "ponto.empresa")
		self.assertEqual(contract.custom_mac_address, "AA:BB:CC:DD:EE:FF")
		self.assertEqual(contract.custom_ipv4_address, "100.64.10.20")

	def test_plan_contains_radius_configuration_directly(self):
		plan = frappe._dict(
			custom_download_mbps=500,
			custom_upload_mbps=250,
			custom_session_limit=1,
			custom_accounting_interval=300,
			custom_radius_attributes='{\"Filter-Id\": \"assinantes\"}',
		)
		validate_internet_plan(plan)
		self.assertEqual(plan.custom_mikrotik_rate_limit, "250M/500M")
		self.assertEqual(json.loads(plan.custom_radius_attributes), {"Filter-Id": "assinantes"})

	def test_full_access_insert_creates_sanitized_outbox_event(self):
		contract = frappe.db.get_value(
			"Subscription",
			{"party_type": "Customer", "status": ["not in", ["Cancelled", "Completed"]]},
			["name", "party"],
			as_dict=True,
		)
		if not contract:
			self.skipTest("No active customer subscription is available on this development site")
		plan = frappe.db.get_value(
			"Subscription Plan Detail",
			{"parent": contract.name, "parenttype": "Subscription"},
			"plan",
			order_by="idx asc",
		)
		if not plan:
			self.skipTest("The selected subscription has no plan")

		suffix = uuid.uuid4().hex[:10]
		profile_name = frappe.db.get_value("Perfil RADIUS", {"plano": plan, "ativo": 1}, "name")
		profile = frappe.get_doc("Perfil RADIUS", profile_name) if profile_name else frappe.get_doc(
			{
				"doctype": "Perfil RADIUS",
				"codigo": f"teste-{suffix}",
				"nome_perfil": f"Teste {suffix}",
				"plano": plan,
				"tipo_perfil": "Normal",
				"download_mbps": 100,
				"upload_mbps": 50,
				"limite_sessoes": 1,
				"acct_interim_interval": 300,
			}
		).insert(ignore_permissions=True)
		access = frappe.get_doc(
			{
				"doctype": "Acesso PPPoE",
				"cliente": contract.party,
				"contrato": contract.name,
				"perfil_radius": profile.name,
				"situacao": "Ativo",
				"usuario_pppoe": f"teste.{suffix}",
				"senha_pppoe": "segredo-transacional",
				"limite_sessoes": 1,
			}
		).insert(ignore_permissions=True)

		event = frappe.db.get_value(
			"Evento de Provisionamento RADIUS",
			{"acesso_pppoe": access.name, "operacao": "Criar"},
			["estado", "versao", "conteudo"],
			as_dict=True,
		)
		self.assertIsNotNone(event)
		self.assertEqual(event.estado, "Pendente")
		self.assertEqual(event.versao, 1)
		self.assertNotIn("segredo-transacional", event.conteudo)

	def test_profile_generates_mikrotik_rate_limit(self):
		profile = frappe.get_doc(
			{
				"doctype": "Perfil RADIUS",
				"codigo": " Fibra 500 ",
				"nome_perfil": "Fibra 500",
				"tipo_perfil": "Normal",
				"download_mbps": 500,
				"upload_mbps": 250,
				"limite_sessoes": 1,
				"acct_interim_interval": 300,
				"atributos_adicionais": '{"Filter-Id": "assinantes"}',
			}
		)
		profile.run_method("validate")

		self.assertEqual(profile.codigo, "fibra-500")
		self.assertEqual(profile.mikrotik_rate_limit, "250M/500M")
		self.assertEqual(json.loads(profile.atributos_adicionais), {"Filter-Id": "assinantes"})

	def test_nas_normalizes_network_values(self):
		nas = frappe.get_doc(
			{
				"doctype": "NAS RADIUS",
				"identificacao": "LAB",
				"endereco_ip": "192.0.2.10",
				"fabricante": "MikroTik",
				"segredo_compartilhado": "teste",
				"rede_confiavel": "192.0.2.15/24",
				"suporta_coa": 1,
				"porta_coa": 1700,
			}
		)
		nas.run_method("validate")

		self.assertEqual(nas.endereco_ip, "192.0.2.10")
		self.assertEqual(nas.rede_confiavel, "192.0.2.0/24")

	def test_access_normalizes_username_mac_and_addresses(self):
		access = frappe.get_doc(
			{
				"doctype": "Acesso PPPoE",
				"usuario_pppoe": " Cliente.Teste ",
				"mac_autorizado": "aa-bb-cc-dd-ee-ff",
				"ipv4_fixo": "192.0.2.20",
				"prefixo_ipv6": "2001:db8:1::1/56",
			}
		)
		access._normalize_username()
		access._normalize_addresses()

		self.assertEqual(access.usuario_pppoe, "cliente.teste")
		self.assertEqual(access.mac_autorizado, "AA:BB:CC:DD:EE:FF")
		self.assertEqual(access.ipv4_fixo, "192.0.2.20")
		self.assertEqual(access.prefixo_ipv6, "2001:db8:1::/56")

	def test_event_payload_never_contains_password(self):
		access = frappe._dict(
			name="PPPOE-00001",
			cliente="CLIENTE",
			contrato="SUB-00001",
			plano="PLANO",
			perfil_radius="fibra-500",
			situacao="Ativo",
			usuario_pppoe="cliente.teste",
			senha_pppoe="segredo-que-nao-pode-vazar",
			limite_sessoes=1,
			versao_provisionamento=1,
		)
		access.get_doc_before_save = lambda: None

		with patch("sol_brasil.radius_provisioning.frappe.get_doc") as get_doc:
			get_doc.return_value.insert.return_value = None
			create_provisioning_event(access, "Criar")

		payload = get_doc.call_args.args[0]
		self.assertNotIn("segredo-que-nao-pode-vazar", payload["conteudo"])
		self.assertNotIn("senha_pppoe", payload["conteudo"])
		self.assertTrue(json.loads(payload["conteudo"])["credencial_alterada"])

	def test_operational_reply_uses_effective_policy_and_rejects_secret_attributes(self):
		attributes = _reply_attributes({
			"rate_limit": "25M/100M", "accounting_interval": 300,
			"ipv4_pool": "assinantes", "filter_id": "internet",
			"additional_attributes": {"Session-Timeout": 3600, "User-Password": "nao-vazar"},
		})
		self.assertEqual(attributes["Mikrotik-Rate-Limit"], "25M/100M")
		self.assertEqual(attributes["Framed-Pool"], "assinantes")
		self.assertNotIn("User-Password", attributes)


def run_smoke_tests():
	"""Allow deterministic execution through `bench execute` in development sites."""
	suite = unittest.defaultTestLoader.loadTestsFromTestCase(TestRadiusModels)
	result = unittest.TextTestRunner(verbosity=2).run(suite)
	if not result.wasSuccessful():
		raise AssertionError(f"RADIUS tests failed: {len(result.failures)} failures, {len(result.errors)} errors")
	return {"tests_run": result.testsRun, "successful": True}
