"""Asynchronous, idempotent projection of ERP contracts into FreeRADIUS SQL."""

import hashlib
import json
import uuid
from contextlib import contextmanager

import frappe
from frappe.utils import add_to_date, cint, now_datetime

ACTIVE_STATUS = "Ativo"
MAX_ATTEMPTS = 10
SAFE_ACCESS_FIELDS = (
	"cliente", "contrato", "plano", "perfil_radius", "situacao", "usuario_pppoe",
	"limite_sessoes", "mac_autorizado", "nas_radius", "grupo_nas", "ipv4_fixo",
	"pool_ipv4", "prefixo_ipv6", "pool_ipv6",
)


def _safe_error(error):
	message = " ".join(str(error).split())[:500]
	for key in ("radius_db_password", "radius_db_user"):
		secret = frappe.conf.get(key)
		if secret:
			message = message.replace(str(secret), "***")
	return message


def _has_contract_fields():
	return frappe.get_meta("Subscription").has_field("custom_radius_provisioning_version")


def _plan_name(contract):
	return contract.get("custom_internet_plan") or frappe.db.get_value(
		"Subscription Plan Detail", {"parent": contract.name, "parenttype": "Subscription"},
		"plan", order_by="idx asc",
	)


def subscription_snapshot(subscription):
	contract = frappe.get_doc("Subscription", subscription) if isinstance(subscription, str) else subscription
	plan_name = _plan_name(contract)
	plan = frappe.get_doc("Subscription Plan", plan_name) if plan_name else frappe._dict()
	try:
		extra = json.loads(plan.get("custom_radius_attributes") or "{}")
	except (TypeError, ValueError):
		extra = {}
	payload = {
		"source": "Subscription", "subscription": contract.name,
		"customer": contract.get("party") if contract.get("party_type") == "Customer" else None,
		"username": (contract.get("custom_pppoe_username") or "").strip().lower(),
		"status": contract.get("custom_connection_status") or "Aguardando instalação",
		"plan": plan_name,
		"rate_limit": contract.get("custom_effective_rate_limit") or plan.get("custom_mikrotik_rate_limit"),
		"session_limit": cint(plan.get("custom_session_limit") or 1),
		"accounting_interval": cint(plan.get("custom_accounting_interval") or 300),
		"ipv4_address": contract.get("custom_ipv4_address"), "ipv4_pool": plan.get("custom_ipv4_pool"),
		"ipv6_pool": plan.get("custom_ipv6_pool"), "filter_id": plan.get("custom_filter_id"),
		"mac_address": contract.get("custom_mac_address"), "additional_attributes": extra,
	}
	return {key: value for key, value in payload.items() if value not in (None, "")}


def _snapshot_hash(payload):
	return hashlib.sha256(json.dumps(payload, sort_keys=True, ensure_ascii=False).encode()).hexdigest()


def _create_event(reference, operation, version, payload):
	event_id = str(uuid.uuid4())
	frappe.get_doc({
		"doctype": "Evento de Provisionamento RADIUS", "id_evento": event_id,
		"operacao": operation, "acesso_pppoe": reference, "versao": version,
		"estado": "Pendente", "tentativas": 0,
		"conteudo": json.dumps(payload, ensure_ascii=False, sort_keys=True),
	}).insert(ignore_permissions=True)
	return event_id


def queue_subscription(doc, method=None, force=False):
	"""Create a secret-free outbox event when the effective projection changed."""
	name = doc if isinstance(doc, str) else doc.name
	if not frappe.db.exists("Subscription", name):
		return
	credential_changed = bool(
		not isinstance(doc, str) and doc.get_doc_before_save()
		and doc.has_value_changed("custom_pppoe_password")
	)
	force = force or credential_changed
	payload = subscription_snapshot(name)
	if not payload.get("username"):
		return
	digest = _snapshot_hash(payload)
	if credential_changed:
		payload["credential_changed"] = True
	if _has_contract_fields():
		current = frappe.db.get_value("Subscription", name,
			["custom_radius_snapshot_hash", "custom_radius_provisioning_version"], as_dict=True)
		if not force and current.custom_radius_snapshot_hash == digest:
			return
		version = cint(current.custom_radius_provisioning_version) + 1
		frappe.db.set_value("Subscription", name, {
			"custom_radius_snapshot_hash": digest, "custom_radius_provisioning_version": version,
			"custom_radius_provisioning_state": "Pendente", "custom_radius_last_error": None,
		}, update_modified=False)
	else:
		versions = frappe.get_all("Evento de Provisionamento RADIUS",
			filters={"acesso_pppoe": name}, pluck="versao", order_by="versao desc", limit=1)
		version = cint(versions[0] if versions else 0) + 1
	return _create_event(name, "Criar" if version == 1 else "Atualizar", version, payload)


def queue_subscription_removal(doc, method=None):
	if not doc.get("custom_pppoe_username"):
		return
	payload = {"source": "Subscription", "subscription": doc.name,
		"username": doc.custom_pppoe_username.strip().lower(), "status": "Cancelado"}
	return _create_event(doc.name, "Remover", cint(doc.get("custom_radius_provisioning_version")) + 1, payload)


def create_provisioning_event(access, operation):
	"""Compatibility outbox for legacy Acesso PPPoE; it is not processed operationally."""
	payload = {field: access.get(field) for field in SAFE_ACCESS_FIELDS}
	previous = access.get_doc_before_save()
	payload["source"] = "Acesso PPPoE"
	payload["credencial_alterada"] = operation == "Criar" or bool(
		previous and previous.get("senha_pppoe") != access.get("senha_pppoe"))
	return _create_event(access.name, operation, cint(access.versao_provisionamento) or 1, payload)


def queue_profile_update(access_name):
	access = frappe.get_doc("Acesso PPPoE", access_name)
	access.versao_provisionamento = cint(access.versao_provisionamento) + 1
	frappe.db.set_value("Acesso PPPoE", access.name, {
		"versao_provisionamento": access.versao_provisionamento,
		"estado_provisionamento": "Pendente", "ultimo_erro_provisionamento": None,
	}, update_modified=False)
	create_provisioning_event(access, "Atualizar")


@contextmanager
def radius_connection():
	import pymysql
	required = ("radius_db_host", "radius_db_name", "radius_db_user", "radius_db_password")
	missing = [key for key in required if not frappe.conf.get(key)]
	if missing:
		raise RuntimeError("Configuração RADIUS ausente: " + ", ".join(missing))
	connection = pymysql.connect(
		host=frappe.conf.radius_db_host, port=cint(frappe.conf.get("radius_db_port") or 3306),
		user=frappe.conf.radius_db_user, password=frappe.conf.radius_db_password,
		database=frappe.conf.radius_db_name, charset="utf8mb4", autocommit=False)
	try:
		yield connection
		connection.commit()
	except Exception:
		connection.rollback()
		raise
	finally:
		connection.close()


def _reply_attributes(payload):
	attributes = {}
	if payload.get("rate_limit") and payload["rate_limit"] != "0M/0M":
		attributes["Mikrotik-Rate-Limit"] = payload["rate_limit"]
	if payload.get("accounting_interval"):
		attributes["Acct-Interim-Interval"] = str(payload["accounting_interval"])
	if payload.get("ipv4_address"):
		attributes["Framed-IP-Address"] = payload["ipv4_address"]
	elif payload.get("ipv4_pool"):
		attributes["Framed-Pool"] = payload["ipv4_pool"]
	if payload.get("ipv6_pool"):
		attributes["Delegated-IPv6-Prefix-Pool"] = payload["ipv6_pool"]
	if payload.get("filter_id"):
		attributes["Filter-Id"] = payload["filter_id"]
	for key, value in payload.get("additional_attributes", {}).items():
		if not any(forbidden in str(key).lower() for forbidden in ("password", "senha", "secret")):
			attributes[str(key)] = str(value)
	return attributes


def _subscription_password(name):
	return frappe.get_doc("Subscription", name).get_password("custom_pppoe_password", raise_exception=False)


def _apply_event(connection, event, payload):
	username = payload.get("username")
	if not username:
		raise ValueError("Evento sem usuário PPPoE")
	with connection.cursor() as cursor:
		cursor.execute("SELECT version,enabled,username FROM sol_radius_sync WHERE source_doctype=%s AND source_name=%s FOR UPDATE",
			("Subscription", event.acesso_pppoe))
		row = cursor.fetchone()
		if row and cint(row[0]) >= cint(event.versao):
			return "obsolete"
		if row and row[2] != username:
			cursor.execute("DELETE FROM radcheck WHERE username=%s", (row[2],))
			cursor.execute("DELETE FROM radreply WHERE username=%s", (row[2],))
		cursor.execute("DELETE FROM radcheck WHERE username=%s", (username,))
		cursor.execute("DELETE FROM radreply WHERE username=%s", (username,))
		active = payload.get("status") == ACTIVE_STATUS and event.operacao != "Remover"
		if active:
			password = _subscription_password(payload.get("subscription"))
			if not password:
				raise ValueError("Contrato sem senha PPPoE protegida")
			checks = [("Cleartext-Password", ":=", password)]
			if cint(payload.get("session_limit")):
				checks.append(("Simultaneous-Use", ":=", str(cint(payload["session_limit"]))))
			if payload.get("mac_address"):
				checks.append(("Calling-Station-Id", "==", payload["mac_address"]))
			cursor.executemany("INSERT INTO radcheck (username,attribute,op,value) VALUES (%s,%s,%s,%s)",
				[(username, *value) for value in checks])
			replies = [(username, key, ":=", value) for key, value in _reply_attributes(payload).items()]
			if replies:
				cursor.executemany("INSERT INTO radreply (username,attribute,op,value) VALUES (%s,%s,%s,%s)", replies)
		cursor.execute("""INSERT INTO sol_radius_sync
			(source_doctype,source_name,username,version,enabled,payload_hash)
			VALUES ('Subscription',%s,%s,%s,%s,%s)
			ON DUPLICATE KEY UPDATE username=VALUES(username),version=VALUES(version),
			enabled=VALUES(enabled),payload_hash=VALUES(payload_hash),synced_at=CURRENT_TIMESTAMP""",
			(event.acesso_pppoe, username, event.versao, 1 if active else 0, _snapshot_hash(payload)))
	return "disconnect" if row and cint(row[1]) and not active else "applied"


def process_pending_events(limit=50):
	limit = max(1, cint(limit))
	fields = ["name", "acesso_pppoe", "operacao", "versao", "conteudo", "tentativas", "proxima_tentativa"]
	events = frappe.get_all("Evento de Provisionamento RADIUS",
		filters={"estado": "Pendente", "tentativas": ["<", MAX_ATTEMPTS]},
		fields=fields, order_by="creation asc", limit_page_length=limit)
	if len(events) < limit:
		events.extend(frappe.get_all("Evento de Provisionamento RADIUS",
		filters={"estado": "Erro", "tentativas": ["<", MAX_ATTEMPTS],
			"proxima_tentativa": ["<=", now_datetime()]},
		fields=["name", "acesso_pppoe", "operacao", "versao", "conteudo", "tentativas", "proxima_tentativa"],
		order_by="proxima_tentativa asc", limit_page_length=limit - len(events)))
	processed = failed = 0
	for row in events:
		if row.proxima_tentativa and row.proxima_tentativa > now_datetime():
			continue
		frappe.db.set_value("Evento de Provisionamento RADIUS", row.name, "estado", "Processando", update_modified=False)
		try:
			payload = json.loads(row.conteudo or "{}")
			if payload.get("source") != "Subscription":
				raise ValueError("Evento legado: reprovisione o contrato Subscription")
			with radius_connection() as connection:
				result = _apply_event(connection, row, payload)
			coa_warning = None
			if result == "disconnect":
				from sol_brasil.radius_coa import disconnect_subscription
				coa = disconnect_subscription(row.acesso_pppoe, payload["username"])
				failures = [item["nas"] for item in coa["results"] if not item.get("accepted")]
				if failures:
					coa_warning = "Provisionado; Disconnect não confirmado por: " + ", ".join(failures)
			frappe.db.set_value("Evento de Provisionamento RADIUS", row.name, {
				"estado": "Concluído", "processado_em": now_datetime(), "mensagem_erro": coa_warning}, update_modified=False)
			if frappe.db.exists("Subscription", row.acesso_pppoe) and _has_contract_fields():
				frappe.db.set_value("Subscription", row.acesso_pppoe, {
					"custom_radius_provisioning_state": "Sincronizado",
					"custom_radius_last_sync": now_datetime(), "custom_radius_last_error": None}, update_modified=False)
			processed += 1
		except Exception as error:
			attempts = cint(row.tentativas) + 1
			message = _safe_error(error)
			frappe.db.set_value("Evento de Provisionamento RADIUS", row.name, {
				"estado": "Erro", "tentativas": attempts, "mensagem_erro": message,
				"proxima_tentativa": add_to_date(now_datetime(), seconds=min(3600, 2 ** attempts * 15))}, update_modified=False)
			if frappe.db.exists("Subscription", row.acesso_pppoe) and _has_contract_fields():
				frappe.db.set_value("Subscription", row.acesso_pppoe, {
					"custom_radius_provisioning_state": "Erro", "custom_radius_last_error": message}, update_modified=False)
			failed += 1
	frappe.db.commit()
	return {"processed": processed, "failed": failed}


def reconcile_radius():
	queued = 0
	for name in frappe.get_all("Subscription", filters={"custom_pppoe_username": ["is", "set"]}, pluck="name"):
		if queue_subscription(name):
			queued += 1
	return {"queued": queued}


@frappe.whitelist()
def migration_audit():
	"""Read-only pre-cutover reconciliation report without returning credentials."""
	frappe.only_for("System Manager")
	rows = frappe.get_all("Subscription", filters={"party_type": "Customer"},
		fields=["name", "party", "custom_pppoe_username", "custom_internet_plan", "custom_connection_status"])
	users = {}
	missing_plan = []
	active_without_user = []
	for row in rows:
		username = (row.custom_pppoe_username or "").strip().lower()
		if username:
			users.setdefault(username, []).append(row.name)
			if not row.custom_internet_plan:
				missing_plan.append(row.name)
		elif row.custom_connection_status == ACTIVE_STATUS:
			active_without_user.append(row.name)
	return {
		"contracts": len(rows), "pppoe_contracts": sum(len(names) for names in users.values()),
		"duplicate_usernames": {user: names for user, names in users.items() if len(names) > 1},
		"missing_plan": missing_plan, "active_without_username": active_without_user,
	}


def synchronize_nas():
	"""Project enabled ERP NAS records into the operational SQL client table."""
	rows = frappe.get_all("NAS RADIUS", fields=["name", "identificacao", "endereco_ip", "fabricante", "ativo"])
	active_names = []
	with radius_connection() as connection:
		with connection.cursor() as cursor:
			for row in rows:
				if not cint(row.ativo):
					continue
				secret = frappe.get_doc("NAS RADIUS", row.name).get_password(
					"segredo_compartilhado", raise_exception=False)
				if not secret:
					continue
				active_names.append(row.endereco_ip)
				cursor.execute("""INSERT INTO nas (nasname,shortname,type,secret,description)
					VALUES (%s,%s,%s,%s,%s) ON DUPLICATE KEY UPDATE shortname=VALUES(shortname),
					type=VALUES(type),secret=VALUES(secret),description=VALUES(description)""",
					(row.endereco_ip, row.identificacao[:32], (row.fabricante or "other").lower(), secret, row.name))
			if active_names:
				placeholders = ",".join(["%s"] * len(active_names))
				cursor.execute(f"DELETE FROM nas WHERE nasname NOT IN ({placeholders})", active_names)
			else:
				cursor.execute("DELETE FROM nas")
	return {"synchronized": len(active_names), "reload_required": True}


@frappe.whitelist()
def radius_health():
	frappe.only_for("System Manager")
	with radius_connection() as connection:
		with connection.cursor() as cursor:
			cursor.execute("SELECT 1")
			cursor.execute("SELECT COUNT(*) FROM sol_radius_sync WHERE enabled=1")
			enabled = cint(cursor.fetchone()[0])
			cursor.execute("SELECT COUNT(*) FROM radacct WHERE acctstoptime IS NULL")
			active_sessions = cint(cursor.fetchone()[0])
	return {
		"database": "ok", "enabled_accounts": enabled, "active_sessions": active_sessions,
		"pending_events": frappe.db.count("Evento de Provisionamento RADIUS", {"estado": "Pendente"}),
		"failed_events": frappe.db.count("Evento de Provisionamento RADIUS", {"estado": "Erro"}),
	}


@frappe.whitelist()
def retry_event(event):
	frappe.has_permission("Evento de Provisionamento RADIUS", "write", event, throw=True)
	frappe.db.set_value("Evento de Provisionamento RADIUS", event,
		{"estado": "Pendente", "tentativas": 0, "proxima_tentativa": None, "mensagem_erro": None})
	return event


@frappe.whitelist()
def retry_failed_events():
	frappe.only_for("System Manager")
	names = frappe.get_all("Evento de Provisionamento RADIUS",
		filters={"estado": "Erro", "tentativas": ["<", MAX_ATTEMPTS]}, pluck="name")
	for name in names:
		frappe.db.set_value("Evento de Provisionamento RADIUS", name,
			{"estado": "Pendente", "proxima_tentativa": None, "mensagem_erro": None}, update_modified=False)
	frappe.db.commit()
	return {"retried": len(names)}
