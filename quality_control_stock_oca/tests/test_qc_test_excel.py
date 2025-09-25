from tempfile import NamedTemporaryFile

from odoo.tests.common import TransactionCase

try:  # pragma: no cover - optional dependency guard
    import openpyxl  # noqa: F401
except ImportError:  # pragma: no cover - handled at runtime
    openpyxl = None


class TestQcTestExcel(TransactionCase):
    def test_export_import_roundtrip(self):
        if openpyxl is None:
            self.skipTest("openpyxl is not available")
        Test = self.env["qc.test"]
        Question = self.env["qc.test.question"]
        Value = self.env["qc.test.question.value"]
        category = self.env.ref("quality_control_oca.qc_test_template_category_generic")
        uom = self.env.ref("uom.product_uom_unit")
        product_template = self.env["product.template"].create(
            {"name": "Excel Product", "default_code": "EXCEL-PT"}
        )
        trigger = self.env["qc.trigger"].create({"name": "Manufacturing Order"})

        test = Test.create(
            {
                "name": "Excel demo",
                "code": "EXCEL-DEMO",
                "category": category.id,
                "fill_correct_values": True,
            }
        )
        qualitative = Question.create(
            {
                "test": test.id,
                "name": "Is it good?",
                "code": "GOOD",
                "type": "qualitative",
                "sequence": 5,
                "notes": "note",
            }
        )
        Value.create({"test_line": qualitative.id, "name": "Yes", "ok": True})
        Value.create({"test_line": qualitative.id, "name": "No", "ok": False})
        Question.create(
            {
                "test": test.id,
                "name": "Length",
                "code": "LEN",
                "type": "quantitative",
                "sequence": 10,
                "min_value": 1.0,
                "max_value": 2.0,
                "uom_id": uom.id,
            }
        )
        self.env["qc.trigger.product_template_line"].create(
            {
                "test": test.id,
                "trigger": trigger.id,
                "product_template": product_template.id,
                "timing": "before",
            }
        )

        with NamedTemporaryFile(suffix=".xlsx") as tmp:
            Test.export_to_excel(tmp.name)
            Test.search([]).unlink()
            Question.search([]).unlink()
            Value.search([]).unlink()
            Test.import_from_excel(tmp.name)

        imported = Test.search([("code", "=", "EXCEL-DEMO")])
        self.assertTrue(imported)
        self.assertEqual(imported.category, category)
        self.assertTrue(imported.fill_correct_values)

        q_field = Test._question_field()
        questions = getattr(imported, q_field)
        self.assertEqual(len(questions), 2)
        questions_by_code = {question.code: question for question in questions}

        qualitative_question = questions_by_code["GOOD"]
        self.assertEqual(qualitative_question.type, "qualitative")
        self.assertEqual(qualitative_question.sequence, 5)
        self.assertEqual(qualitative_question.notes, "note")
        self.assertEqual(
            {value.name for value in qualitative_question.ql_values},
            {"Yes", "No"},
        )
        self.assertTrue(
            qualitative_question.ql_values.filtered(lambda value: value.name == "Yes").ok
        )

        quantitative_question = questions_by_code["LEN"]
        self.assertEqual(quantitative_question.type, "quantitative")
        self.assertEqual(quantitative_question.uom_id, uom)
        self.assertEqual(quantitative_question.min_value, 1.0)
        self.assertEqual(quantitative_question.max_value, 2.0)

        trigger_lines = self.env["qc.trigger.product_template_line"].search(
            [
                ("test", "=", imported.id),
                ("product_template", "=", product_template.id),
            ]
        )
        self.assertEqual(len(trigger_lines), 1)
        imported_trigger = trigger_lines[0]
        self.assertEqual(imported_trigger.trigger.name, trigger.name)
        self.assertEqual(imported_trigger.timing, "before")

    def test_export_import_wizards(self):
        if openpyxl is None:
            self.skipTest("openpyxl is not available")
        Test = self.env["qc.test"]
        Question = self.env["qc.test.question"]
        Value = self.env["qc.test.question.value"]

        test = Test.create({"name": "Wizard demo", "code": "WZRD"})
        Question.create({"test": test.id, "name": "Ok?", "code": "OK", "type": "qualitative"})

        wiz_export = (
            self.env["qc.test.export.wizard"].with_context(active_ids=test.ids).create({})
        )
        action = wiz_export.action_export()
        self.assertTrue(action)
        self.assertIn("qc.export.excel.wizard", action.get("url", ""))
        self.assertTrue(wiz_export.file_data)
        self.assertTrue(wiz_export.file_name)

        data = wiz_export.file_data

        Test.search([]).unlink()
        Question.search([]).unlink()
        Value.search([]).unlink()

        wiz_import = self.env["qc.test.import.wizard"].create(
            {"file_data": data, "file_name": wiz_export.file_name}
        )
        wiz_import.action_import()

        imported = Test.search([("name", "=", "Wizard demo")])
        self.assertTrue(imported)
        q_field = Test._question_field()
        question = getattr(imported, q_field)
        self.assertEqual(question.mapped("name"), ["Ok?"])
