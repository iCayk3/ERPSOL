from unittest import TestCase

from sol_brasil.customer import format_cpf_cnpj, is_valid_cnpj, is_valid_cpf


class TestBrazilianDocuments(TestCase):
	def test_valid_cpf(self):
		self.assertTrue(is_valid_cpf("529.982.247-25"))

	def test_invalid_cpf(self):
		self.assertFalse(is_valid_cpf("111.111.111-11"))
		self.assertFalse(is_valid_cpf("529.982.247-24"))

	def test_valid_cnpj(self):
		self.assertTrue(is_valid_cnpj("04.252.011/0001-10"))

	def test_invalid_cnpj(self):
		self.assertFalse(is_valid_cnpj("11.111.111/1111-11"))
		self.assertFalse(is_valid_cnpj("04.252.011/0001-11"))

	def test_formatting(self):
		self.assertEqual(format_cpf_cnpj("52998224725"), "529.982.247-25")
		self.assertEqual(format_cpf_cnpj("04252011000110"), "04.252.011/0001-10")
