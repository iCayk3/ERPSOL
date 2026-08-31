"""Read-only operational accounting queries exposed in the contract form."""

import frappe
from frappe.utils import cint

from sol_brasil.radius_provisioning import radius_connection


@frappe.whitelist()
def get_subscription_sessions(subscription, limit=20):
	frappe.has_permission("Subscription", "read", subscription, throw=True)
	username = frappe.db.get_value("Subscription", subscription, "custom_pppoe_username")
	if not username:
		return {"username": None, "active": [], "recent": [], "totals": {"input": 0, "output": 0}}
	with radius_connection() as connection:
		with connection.cursor() as cursor:
			cursor.execute("""SELECT acctsessionid,nasipaddress,framedipaddress,callingstationid,
				acctstarttime,acctupdatetime,acctinputoctets,acctoutputoctets
				FROM radacct WHERE username=%s AND acctstoptime IS NULL ORDER BY acctstarttime DESC LIMIT %s""",
				(username, cint(limit)))
			active = cursor.fetchall()
			cursor.execute("""SELECT acctsessionid,nasipaddress,framedipaddress,acctstarttime,acctstoptime,
				acctsessiontime,acctinputoctets,acctoutputoctets,acctterminatecause
				FROM radacct WHERE username=%s ORDER BY radacctid DESC LIMIT %s""", (username, cint(limit)))
			recent = cursor.fetchall()
			cursor.execute("SELECT COALESCE(SUM(acctinputoctets),0),COALESCE(SUM(acctoutputoctets),0) FROM radacct WHERE username=%s", (username,))
			totals = cursor.fetchone()
	return {"username": username, "active": active, "recent": recent,
		"totals": {"input": cint(totals[0]), "output": cint(totals[1])}}
