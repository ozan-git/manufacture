from tempfile import NamedTemporaryFile

from odoo.tests.common import TransactionCase


class TestQcTestExcel(TransactionCase):
    def test_export_import_roundtrip(self):
        Test = self.env["qc.test"]
        Question = self.env["qc.test.question"]
        uom = self.env.ref("uom.product_uom_unit")
        test = Test.create({"name": "Excel demo"})
        question = Question.create(
            {
                "test_id": test.id,
                "name": "Is it good?",
                "type": "qualitative",
                "min_value": 1,
                "max_value": 2,
                "uom_id": uom.id,
                "sequence": 5,
                "notes": "note",
            }
        )
        ans_field = Test._answer_field()
        if ans_field:
            AnswerModel = Question._fields[ans_field].comodel_name
            Answer = self.env[AnswerModel]
            rel_field = None
            for fname, field in Answer._fields.items():
                if field.type == "many2one" and field.comodel_name == Question._name:
                    rel_field = fname
                    break
            vals = {"name": "Yes"}
            if rel_field:
                vals[rel_field] = question.id
            Answer.create(vals)
        with NamedTemporaryFile(suffix=".xlsx") as tmp:
            Test.export_to_excel(tmp.name)
            Test.search([]).unlink()
            Question.search([]).unlink()
            Test.import_from_excel(tmp.name)
        imported = Test.search([("name", "=", "Excel demo")])
        self.assertTrue(imported)
        q_field = Test._question_field()
        question = getattr(imported, q_field)
        self.assertEqual(question.mapped("name"), ["Is it good?"])
        self.assertEqual(question.type, "qualitative")
        self.assertEqual(question.min_value, 1)
        self.assertEqual(question.max_value, 2)
        self.assertEqual(question.uom_id, uom)
        self.assertEqual(question.sequence, 5)
        self.assertEqual(question.notes, "note")
        if ans_field:
            self.assertEqual(getattr(question, ans_field).mapped("name"), ["Yes"])

    def test_export_import_wizards(self):
        Test = self.env["qc.test"]
        Question = self.env["qc.test.question"]
        test = Test.create({"name": "Wizard demo"})
        question = Question.create({"test_id": test.id, "name": "Ok?"})
        ans_field = Test._answer_field()
        if ans_field:
            AnswerModel = Question._fields[ans_field].comodel_name
            Answer = self.env[AnswerModel]
            rel_field = None
            for fname, field in Answer._fields.items():
                if field.type == "many2one" and field.comodel_name == Question._name:
                    rel_field = fname
                    break
            vals = {"name": "A"}
            if rel_field:
                vals[rel_field] = question.id
            Answer.create(vals)
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
        q_field = Test._question_field()
        question = getattr(imported, q_field)
        self.assertEqual(question.mapped("name"), ["Ok?"])
        if ans_field:
            self.assertEqual(getattr(question, ans_field).mapped("name"), ["A"])
