"""Minimal RFC 5176 Disconnect-Request client for enabled NAS records."""

import hashlib
import os
import socket
import struct
import time

import frappe
from frappe.utils import cint


def _attribute(kind, value):
	data = value if isinstance(value, bytes) else str(value).encode()
	return bytes((kind, len(data) + 2)) + data


def disconnect(nas_ip, port, secret, username, timeout=2):
	identifier = os.urandom(1)[0]
	attributes = _attribute(1, username) + _attribute(55, struct.pack("!I", int(time.time())))
	length = 20 + len(attributes)
	header = struct.pack("!BBH", 40, identifier, length)
	authenticator = hashlib.md5(header + (b"\0" * 16) + attributes + secret.encode()).digest()
	request = header + authenticator + attributes
	with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as client:
		client.settimeout(timeout)
		client.sendto(request, (nas_ip, cint(port) or 3799))
		response, _ = client.recvfrom(4096)
	if len(response) < 20 or response[0] not in (41, 42) or response[1] != identifier:
		raise RuntimeError("Resposta CoA/Disconnect inválida")
	expected = hashlib.md5(response[:4] + authenticator + response[20:] + secret.encode()).digest()
	if expected != response[4:20]:
		raise RuntimeError("Assinatura da resposta CoA/Disconnect inválida")
	return response[0] == 41


def disconnect_subscription(subscription, username):
	results = []
	for row in frappe.get_all("NAS RADIUS", filters={"ativo": 1, "suporta_coa": 1},
		fields=["name", "endereco_ip", "porta_coa"]):
		secret = frappe.get_doc("NAS RADIUS", row.name).get_password("segredo_compartilhado", raise_exception=False)
		if not secret:
			continue
		try:
			accepted = disconnect(row.endereco_ip, row.porta_coa, secret, username)
			results.append({"nas": row.name, "accepted": accepted})
		except (OSError, RuntimeError) as error:
			results.append({"nas": row.name, "accepted": False, "error": str(error)[:200]})
	return {"subscription": subscription, "results": results}
