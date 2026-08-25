import re
import secrets
import socket
import time
from dataclasses import dataclass
from datetime import datetime

import frappe
from frappe import _
from frappe.rate_limiter import rate_limit
from frappe.utils import cint, flt, now_datetime


SETTINGS_DOCTYPE = "Configurações FiberHome UNM"
LOG_DOCTYPE = "Operação FiberHome"
QUERY_ROLES = {"Consulta de Rede FiberHome", "Operação de Rede FiberHome", "Administração FiberHome", "System Manager"}
OPERATE_ROLES = {"Operação de Rede FiberHome", "Administração FiberHome", "System Manager"}
ADMIN_ROLES = {"Administração FiberHome", "System Manager"}
AUTH_TYPES = {"MAC", "LOID", "LOIDONCEON"}
ONU_ID_TYPES = {"MAC", "LOID", "ONU_NUMBER", "ONU_NAME"}
SAFE_VALUE = re.compile(r"^[A-Za-z0-9_.@/ -]{1,128}$")
MAC_VALUE = re.compile(r"^(?:(?:[0-9A-Fa-f]{2}[-:]){5}[0-9A-Fa-f]{2}|[A-Za-z0-9]{8,32})$")
PON_VALUE = re.compile(r"^(?:NA|\d+)-(?:NA|\d+)-(?:NA|\d+)-(?:NA|\d+)$", re.IGNORECASE)


class TL1Error(Exception):
	pass


@dataclass(frozen=True)
class TL1Result:
	ctag: str
	command: str
	response: str


def _require_role(allowed):
	if not set(frappe.get_roles()).intersection(allowed):
		frappe.throw(_("Você não possui permissão para esta operação de rede."), frappe.PermissionError)


def _require_post():
	if frappe.request and frappe.request.method != "POST":
		frappe.throw(_("Esta operação aceita somente requisições POST."), frappe.PermissionError)


def _safe(value, label, *, pattern=SAFE_VALUE, maximum=128, required=True):
	value = str(value or "").strip()
	if required and not value:
		frappe.throw(_("{0} é obrigatório.").format(label))
	if value and (len(value) > maximum or not pattern.fullmatch(value)):
		frappe.throw(_("{0} possui formato inválido.").format(label))
	return value


def _sanitize(text):
	return re.sub(r"(?i)(PWD=)[^,;\r\n]*", r"\1***", text or "")


def _safe_secret(value, label, maximum=128):
	value = str(value or "")
	if not value or len(value) > maximum or any(character in value for character in ",;:\r\n"):
		frappe.throw(_("{0} possui formato inválido para TL1.").format(label))
	return value


def _ctag():
	return secrets.token_hex(8).upper()


class TL1Client:
	def __init__(self, host, port, username, password, timeout=8):
		self.host = host
		self.port = int(port)
		self.username = username
		self.password = password
		self.timeout = max(2, min(int(timeout), 30))
		self._socket = None
		self._buffer = b""

	def __enter__(self):
		try:
			self._socket = socket.create_connection((self.host, self.port), timeout=self.timeout)
			self._socket.settimeout(self.timeout)
			login_ctag = _ctag()
			response = self._exchange(f"LOGIN:::{login_ctag}::UN={self.username},PWD={self.password};")
			self._assert_completed(response)
			return self
		except Exception:
			self.close()
			raise

	def __exit__(self, *_):
		if self._socket:
			try:
				logout_ctag = _ctag()
				self._exchange(f"LOGOUT:::{logout_ctag}::;")
			except (OSError, TL1Error):
				pass
		self.close()

	def close(self):
		if self._socket:
			self._socket.close()
			self._socket = None

	def execute(self, command):
		response = self._exchange(command)
		self._assert_completed(response)
		return response

	def _exchange(self, command):
		if not self._socket:
			raise TL1Error(_("Conexão TL1 não inicializada."))
		try:
			self._socket.sendall(command.encode("ascii"))
		except UnicodeEncodeError as exc:
			raise TL1Error(_("O comando TL1 contém caracteres não suportados.")) from exc

		while b";" not in self._buffer:
			chunk = self._socket.recv(16384)
			if not chunk:
				raise TL1Error(_("O UNM encerrou a conexão antes de concluir a resposta."))
			self._buffer += chunk
			if len(self._buffer) > 1024 * 1024:
				raise TL1Error(_("A resposta TL1 excedeu o limite de segurança."))

		packet, self._buffer = self._buffer.split(b";", 1)
		return packet.decode("utf-8", errors="replace") + ";"

	@staticmethod
	def _assert_completed(response):
		if not re.search(r"\bCOMPLD\b", response, re.IGNORECASE):
			description = re.search(r"ENDESC=([^\r\n;]+)", response, re.IGNORECASE)
			raise TL1Error(description.group(1).strip() if description else _("Operação recusada pelo UNM."))
		error = re.search(r"\bEN=([^\s;]+)", response, re.IGNORECASE)
		if error and error.group(1) not in {"0", "NO_ERROR"}:
			raise TL1Error(_("O UNM retornou erro {0}.").format(error.group(1)))


def _settings():
	settings = frappe.get_single(SETTINGS_DOCTYPE)
	if not settings.enabled:
		frappe.throw(_("A integração FiberHome está desabilitada."))
	host = _safe(settings.host, _("Host do UNM"), maximum=253)
	port = cint(settings.port)
	if not 1 <= port <= 65535:
		frappe.throw(_("A porta TL1 configurada é inválida."))
	password = settings.get_password("password", raise_exception=False)
	if not settings.username or not password:
		frappe.throw(_("Configure o usuário e a senha TL1 do UNM."))
	return settings, password


def _client():
	settings, password = _settings()
	return TL1Client(settings.host, settings.port, settings.username, password, settings.timeout_seconds)


@frappe.whitelist()
@rate_limit(limit=5, seconds=60, methods="POST")
def test_connection():
	_require_post()
	_require_role(ADMIN_ROLES)
	started = time.monotonic()
	try:
		with _client():
			pass
	except (OSError, TL1Error) as exc:
		frappe.throw(_("Não foi possível conectar e autenticar no UNM: {0}").format(str(exc)))
	return {"connected": True, "latency_ms": round((time.monotonic() - started) * 1000)}


def _customer_context(customer):
	frappe.has_permission("Customer", "read", customer, throw=True)
	doc = frappe.get_doc("Customer", customer)
	if not doc.custom_olt:
		frappe.throw(_("Vincule uma OLT ao cliente."))
	olt = frappe.get_doc("OLT", doc.custom_olt)
	olt_id = _safe(olt.tl1_olt_id or olt.ip_gerenciamento, _("Identificador TL1 da OLT"))
	slot = _safe(doc.custom_olt_slot, _("Slot"), pattern=re.compile(r"^\d+$"), maximum=3)
	pon = _safe(doc.custom_pon_port or doc.custom_pon, _("Porta PON"), pattern=re.compile(r"^\d+$"), maximum=3)
	pon_id = f"NA-NA-{slot}-{pon}"
	_safe(pon_id, _("PONID"), pattern=PON_VALUE)
	return doc, olt_id, pon_id


def _onu_identity(doc):
	id_type = (doc.custom_onu_id_type or "MAC").upper()
	if id_type not in ONU_ID_TYPES:
		frappe.throw(_("Tipo de identificador da ONU inválido."))
	identifier = doc.custom_onu_serial if id_type == "MAC" else doc.custom_onu_id
	pattern = MAC_VALUE if id_type == "MAC" else SAFE_VALUE
	identifier = _safe(identifier, _("Identificador da ONU"), pattern=pattern)
	if id_type == "MAC":
		identifier = identifier.replace(":", "-").upper()
	return id_type, identifier


def _new_log(customer, operation, command, ctag, status="Em andamento"):
	return frappe.get_doc({
		"doctype": LOG_DOCTYPE,
		"customer": customer,
		"operation": operation,
		"ctag": ctag,
		"status": status,
		"requested_by": frappe.session.user,
		"started_at": now_datetime(),
		"command_summary": _sanitize(command),
	}).insert(ignore_permissions=True)


def _finish_log(log_name, status, response="", error=""):
	frappe.db.set_value(LOG_DOCTYPE, log_name, {
		"status": status,
		"finished_at": now_datetime(),
		"response_summary": _sanitize(response)[:10000],
		"error_message": str(error)[:1000],
	}, update_modified=False)


def _run_logged(customer, operation, command, ctag):
	log = _new_log(customer, operation, command, ctag)
	try:
		with _client() as client:
			response = client.execute(command)
		_finish_log(log.name, "Concluída", response=response)
		return TL1Result(ctag, command, response), log.name
	except Exception as exc:
		_finish_log(log.name, "Falhou", error=exc)
		raise


def _parse_optical_power(response):
	for line in reversed(response.splitlines()):
		parts = line.split()
		if len(parts) >= 5 and re.fullmatch(r"-?\d+(?:\.\d+)?", parts[1] or ""):
			return {
				"onu_number": parts[0],
				"rx_power": flt(parts[1]),
				"rx_status": parts[2],
				"tx_power": flt(parts[3]),
				"tx_status": parts[4],
			}
	raise TL1Error(_("Não foi possível interpretar a potência óptica retornada pelo UNM."))


@frappe.whitelist()
@rate_limit(limit=30, seconds=60, methods="POST")
def query_signal(customer):
	_require_post()
	_require_role(QUERY_ROLES)
	doc, olt_id, pon_id = _customer_context(customer)
	id_type, identifier = _onu_identity(doc)
	ctag = _ctag()
	command = f"LST-OMDDM::OLTID={olt_id},PONID={pon_id},ONUIDTYPE={id_type},ONUID={identifier}:{ctag}::;"
	result, operation = _run_logged(customer, "Consultar sinal", command, ctag)
	power = _parse_optical_power(result.response)
	frappe.db.set_value("Customer", customer, {
		"custom_onu_rx_signal": power["rx_power"],
		"custom_onu_tx_signal": power["tx_power"],
		"custom_onu_signal_status": f"RX {power['rx_status']} / TX {power['tx_status']}",
		"custom_onu_signal_checked_at": now_datetime(),
	}, update_modified=False)
	return {**power, "operation": operation}


@frappe.whitelist()
@rate_limit(limit=10, seconds=60, methods="POST")
def authorize_onu(customer):
	_require_post()
	_require_role(OPERATE_ROLES)
	doc, olt_id, pon_id = _customer_context(customer)
	auth_type = (doc.custom_onu_auth_type or "MAC").upper()
	if auth_type not in AUTH_TYPES:
		frappe.throw(_("Modo de autenticação inválido."))
	identifier = doc.custom_onu_serial if auth_type == "MAC" else doc.custom_onu_id
	identifier = _safe(identifier, _("Identificador da ONU"), pattern=MAC_VALUE if auth_type == "MAC" else SAFE_VALUE)
	password = doc.get_password("custom_onu_auth_password", raise_exception=False) if auth_type != "MAC" else ""
	model = _safe(doc.custom_onu_model, _("Modelo da ONU"), maximum=32)
	onu_number = cint(doc.custom_onu_number)
	if not 1 <= onu_number <= 512:
		frappe.throw(_("O número da ONU deve estar entre 1 e 512."))
	ctag = _ctag()
	params = [f"AUTHTYPE={auth_type}", f"ONUID={identifier}"]
	if password:
		params.append(f"PWD={_safe_secret(password, _('Senha LOID'))}")
	params.extend([f"ONUNO={onu_number}", f"NAME=ONU{onu_number}", f"ONUTYPE={model}"])
	command = f"ADD-ONU::OLTID={olt_id},PONID={pon_id}:{ctag}::" + ",".join(params) + ";"
	result, operation = _run_logged(customer, "Autorizar ONU", command, ctag)
	return {"operation": operation, "ctag": result.ctag}


@frappe.whitelist()
@rate_limit(limit=5, seconds=60, methods="POST")
def deauthorize_onu(customer, confirmation):
	_require_post()
	_require_role(OPERATE_ROLES)
	if confirmation != customer:
		frappe.throw(_("A confirmação da desautorização não confere com o cliente."))
	doc, olt_id, pon_id = _customer_context(customer)
	id_type, identifier = _onu_identity(doc)
	ctag = _ctag()
	command = f"DEL-ONU::OLTID={olt_id},PONID={pon_id}:{ctag}::ONUIDTYPE={id_type},ONUID={identifier};"
	result, operation = _run_logged(customer, "Desautorizar ONU", command, ctag)
	return {"operation": operation, "ctag": result.ctag}
