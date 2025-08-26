from tempfile import NamedTemporaryFile

from odoo.tests.common import TransactionCase


class TestQcTestExcel(TransactionCase):
    def test_export_import_roundtrip(self):
        Test = self.env["qc.test"]
        Question = self.env["qc.test.question"]
        test = Test.create({"name": "Excel demo"})
        Question.create({"test_id": test.id, "question": "Is it good?"})
        with NamedTemporaryFile(suffix=".xlsx") as tmp:
            Test.export_to_excel(tmp.name)
            Test.search([]).unlink()
            Question.search([]).unlink()
            Test.import_from_excel(tmp.name)
        imported = Test.search([("name", "=", "Excel demo")])
        self.assertTrue(imported)
        self.assertEqual(
            imported.question_ids.mapped("question"),
            ["Is it good?"],
        )
