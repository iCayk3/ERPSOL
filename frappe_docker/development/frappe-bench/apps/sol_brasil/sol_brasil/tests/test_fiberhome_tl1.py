from unittest import TestCase

from sol_brasil.fiberhome_tl1 import TL1Client, TL1Error, _parse_optical_power, _sanitize


class TestFiberHomeTL1(TestCase):
	def test_sanitizes_every_tl1_password(self):
		self.assertEqual(
			_sanitize("LOGIN:::ABC::UN=user,PWD=secret;"),
			"LOGIN:::ABC::UN=user,PWD=***;",
		)
		self.assertEqual(_sanitize("ADD-ONU::X:Y::ONUID=A,PWD=loid123,ONUNO=1;"), "ADD-ONU::X:Y::ONUID=A,PWD=***,ONUNO=1;")

	def test_parses_optical_power_row(self):
		response = """
M CTAG COMPLD
List of Optical Power Info
ONUID RxPower RxPowerR TxPower TxPowerR CurrTxBias
5 -9.76 Normal 1.76 Normal 15.80 Normal 62.37 Normal 3.40 Normal -- --
;"""
		self.assertEqual(_parse_optical_power(response), {
			"onu_number": "5",
			"rx_power": -9.76,
			"rx_status": "Normal",
			"tx_power": 1.76,
			"tx_status": "Normal",
		})

	def test_rejects_incomplete_response(self):
		with self.assertRaises(TL1Error):
			TL1Client._assert_completed("M CTAG DENY\nEN=IIPE ENDESC=input parameter error;")
