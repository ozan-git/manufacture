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

    def test_export_import_wizards(self):
        Test = self.env["qc.test"]
        Question = self.env["qc.test.question"]
        test = Test.create({"name": "Wizard demo"})
        Question.create({"test_id": test.id, "question": "Ok?"})
        wiz_export = (
            self.env["qc.test.export.wizard"]
            .with_context(active_ids=test.ids)
            .create({})
        )
        wiz_export.action_export()
        data = wiz_export.file_data
        Test.search([]).unlink()
        Question.search([]).unlink()
        wiz_import = self.env["qc.test.import.wizard"].create({"file_data": data})
        wiz_import.action_import()
        imported = Test.search([("name", "=", "Wizard demo")])
        self.assertTrue(imported)
        self.assertEqual(imported.question_ids.mapped("question"), ["Ok?"])
