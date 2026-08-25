import re
from ipaddress import ip_address, ip_network

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import cint


PROVISIONING_FIELDS = {
	"cliente",
	"contrato",
	"perfil_radius",
	"situacao",
	"usuario_pppoe",
	"senha_pppoe",
	"limite_sessoes",
	"mac_autorizado",
	"nas_radius",
	"grupo_nas",
	"ipv4_fixo",
	"pool_ipv4",
	"prefixo_ipv6",
	"pool_ipv6",
}


class AcessoPPPoE(Document):
	def validate(self):
		self._normalize_username()
		self._validate_contract()
		self._validate_profile()
		self._validate_session_limit()
		self._normalize_addresses()
		self._set_operational_state()
		self._set_provisioning_version()

	def after_insert(self):
		self._create_provisioning_event("Criar")

	def on_update(self):
		if self.flags.in_insert or not self._provisioning_changed():
			return
		self._create_provisioning_event(self._event_operation())

	def on_trash(self):
		self._create_provisioning_event("Remover")

	def _normalize_username(self):
		self.usuario_pppoe = (self.usuario_pppoe or "").strip().lower()
		if not self.usuario_pppoe or any(character.isspace() for character in self.usuario_pppoe):
			frappe.throw(_("Informe um usuário PPPoE válido, sem espaços."))

	def _validate_contract(self):
		contract = frappe.db.get_value(
			"Subscription",
			self.contrato,
			["party_type", "party", "status"],
			as_dict=True,
		)
		if not contract or contract.party_type != "Customer" or contract.party != self.cliente:
			frappe.throw(
				_("O contrato selecionado não pertence a este cliente."),
				title=_("Contrato inválido"),
			)
		if contract.status in ("Cancelled", "Completed") and self.situacao != "Cancelado":
			frappe.throw(
				_("Um contrato cancelado ou concluído só pode permanecer em um acesso cancelado."),
				title=_("Contrato indisponível"),
			)

		plans = frappe.get_all(
			"Subscription Plan Detail",
			filters={"parent": self.contrato, "parenttype": "Subscription"},
			pluck="plan",
			order_by="idx asc",
		)
		self.plano = plans[0] if plans else None

	def _validate_profile(self):
		if not self.plano:
			frappe.throw(
				_("O contrato precisa possuir um plano de internet para definir o perfil RADIUS."),
				title=_("Plano obrigatório"),
			)
		self.perfil_radius = frappe.db.get_value(
			"Perfil RADIUS", {"plano": self.plano, "ativo": 1}, "name"
		)
		if not self.perfil_radius:
			frappe.throw(
				_("O plano {0} ainda não possui um perfil RADIUS ativo associado.").format(
					frappe.bold(self.plano)
				),
				title=_("Perfil RADIUS obrigatório"),
			)

	def _validate_session_limit(self):
		if cint(self.limite_sessoes) < 1:
			frappe.throw(_("O limite de sessões simultâneas deve ser pelo menos 1."))

	def _normalize_addresses(self):
		if self.ipv4_fixo:
			try:
				address = ip_address(self.ipv4_fixo.strip())
			except ValueError:
				frappe.throw(_("Informe um endereço IPv4 fixo válido."))
			if address.version != 4:
				frappe.throw(_("O campo IPv4 fixo aceita somente endereços IPv4."))
			self.ipv4_fixo = str(address)

		if self.prefixo_ipv6:
			try:
				network = ip_network(self.prefixo_ipv6.strip(), strict=False)
			except ValueError:
				frappe.throw(_("Informe um prefixo IPv6 válido."))
			if network.version != 6:
				frappe.throw(_("O campo Prefixo IPv6 aceita somente redes IPv6."))
			self.prefixo_ipv6 = str(network)

		if self.mac_autorizado:
			hexadecimal = re.sub(r"[^0-9A-Fa-f]", "", self.mac_autorizado)
			if len(hexadecimal) != 12:
				frappe.throw(_("Informe um endereço MAC válido com 12 dígitos hexadecimais."))
			self.mac_autorizado = ":".join(
				hexadecimal[index : index + 2].upper() for index in range(0, 12, 2)
			)

	def _set_operational_state(self):
		self.ativo = 0 if self.situacao == "Cancelado" else 1

	def _provisioning_changed(self):
		previous = self.get_doc_before_save()
		return bool(previous) and any(previous.get(field) != self.get(field) for field in PROVISIONING_FIELDS)

	def _set_provisioning_version(self):
		previous = self.get_doc_before_save()
		if not previous:
			self.versao_provisionamento = 1
			return
		if any(previous.get(field) != self.get(field) for field in PROVISIONING_FIELDS):
			self.versao_provisionamento = cint(previous.versao_provisionamento) + 1
			self.estado_provisionamento = "Pendente"
			self.ultimo_erro_provisionamento = None

	def _event_operation(self):
		previous = self.get_doc_before_save()
		if self.situacao == "Cancelado":
			return "Cancelar"
		if previous and previous.situacao != self.situacao:
			if self.situacao in ("Bloqueado financeiramente", "Suspenso tecnicamente"):
				return "Bloquear"
			if previous.situacao in ("Bloqueado financeiramente", "Suspenso tecnicamente"):
				return "Desbloquear"
		return "Atualizar"

	def _create_provisioning_event(self, operation):
		from sol_brasil.radius_provisioning import create_provisioning_event

		create_provisioning_event(self, operation)
