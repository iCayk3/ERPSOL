import json
import uuid

import frappe
from frappe.utils import cint


SAFE_ACCESS_FIELDS = (
	"cliente",
	"contrato",
	"plano",
	"perfil_radius",
	"situacao",
	"usuario_pppoe",
	"limite_sessoes",
	"mac_autorizado",
	"nas_radius",
	"grupo_nas",
	"ipv4_fixo",
	"pool_ipv4",
	"prefixo_ipv6",
	"pool_ipv6",
)


def create_provisioning_event(access, operation):
	"""Persist an outbox event without copying the PPPoE password to logs or payloads."""
	payload = {field: access.get(field) for field in SAFE_ACCESS_FIELDS}
	previous = access.get_doc_before_save()
	payload["credencial_alterada"] = operation == "Criar" or bool(
		previous and previous.get("senha_pppoe") != access.get("senha_pppoe")
	)
	frappe.get_doc(
		{
			"doctype": "Evento de Provisionamento RADIUS",
			"id_evento": str(uuid.uuid4()),
			"operacao": operation,
			"acesso_pppoe": access.name,
			"versao": cint(access.versao_provisionamento) or 1,
			"estado": "Pendente",
			"tentativas": 0,
			"conteudo": json.dumps(payload, ensure_ascii=False, sort_keys=True),
		}
	).insert(ignore_permissions=True)


def queue_profile_update(access_name):
	"""Queue updated profile attributes for an access without rewriting its secret."""
	access = frappe.get_doc("Acesso PPPoE", access_name)
	access.versao_provisionamento = cint(access.versao_provisionamento) + 1
	access.estado_provisionamento = "Pendente"
	access.ultimo_erro_provisionamento = None
	frappe.db.set_value(
		"Acesso PPPoE",
		access.name,
		{
			"versao_provisionamento": access.versao_provisionamento,
			"estado_provisionamento": access.estado_provisionamento,
			"ultimo_erro_provisionamento": None,
		},
		update_modified=False,
	)
	create_provisioning_event(access, "Atualizar")
