from tempfile import NamedTemporaryFile

from odoo.tests.common import TransactionCase


class TestQcTestExcel(TransactionCase):
    def test_export_import_roundtrip(self):
        Test = self.env["qc.test"]
        Test.create({"name": "Excel demo"})
        with NamedTemporaryFile(suffix=".xlsx") as tmp:
            Test.export_to_excel(tmp.name)
            Test.search([]).unlink()
            Test.import_from_excel(tmp.name)
        self.assertTrue(Test.search([("name", "=", "Excel demo")]))
