from tempfile import NamedTemporaryFile

from odoo.tests.common import TransactionCase


class TestQcTestExcel(TransactionCase):
    def test_export_import_roundtrip(self):
        Test = self.env["qc.test"]
        Question = self.env["qc.test.question"]
        uom = self.env.ref("uom.product_uom_unit")
        test = Test.create({"name": "Excel demo"})
        Question.create(
            {
                "test_id": test.id,
                "name": "Is it good?",
                "type": "qualitative",
                "min": 1,
                "max": 2,
                "uom_id": uom.id,
                "sequence": 5,
                "notes": "note",
            }
        )
        with NamedTemporaryFile(suffix=".xlsx") as tmp:
            Test.export_to_excel(tmp.name)
            Test.search([]).unlink()
            Question.search([]).unlink()
            Test.import_from_excel(tmp.name)
        imported = Test.search([("name", "=", "Excel demo")])
        self.assertTrue(imported)
        question = imported.question_ids
        self.assertEqual(question.mapped("name"), ["Is it good?"])
        self.assertEqual(question.type, "qualitative")
        self.assertEqual(question.min, 1)
        self.assertEqual(question.max, 2)
        self.assertEqual(question.uom_id, uom)
        self.assertEqual(question.sequence, 5)
        self.assertEqual(question.notes, "note")

    def test_export_import_wizards(self):
        Test = self.env["qc.test"]
        Question = self.env["qc.test.question"]
        test = Test.create({"name": "Wizard demo"})
        Question.create({"test_id": test.id, "name": "Ok?"})
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
        self.assertEqual(imported.question_ids.mapped("name"), ["Ok?"])
