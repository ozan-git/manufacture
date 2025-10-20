# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import base64
import io

from odoo.tests.common import TransactionCase

try:  # pragma: no cover - optional dependency guard
    from openpyxl import Workbook
except ImportError:  # pragma: no cover - handled in tests
    Workbook = None


HEADERS = [
    "name",
    "test_lines/name",
    "test_lines/type",
    "test_lines/notes",
    "test_lines/ql_values/name",
    "test_lines/ql_values/ok",
    "test_lines/min_value",
    "test_lines/max_value",
    "test_lines/uom",
]


class TestQcExcelLoader(TransactionCase):
    def setUp(self):
        super().setUp()
        if Workbook is None:
            self.skipTest("openpyxl is not available")
        self.loader = self.env["qc.excel.loader"]
        self.unit_uom = self.env.ref("uom.product_uom_unit")

    def _build_workbook(self, rows, headers=HEADERS):
        workbook = Workbook()
        sheet = workbook.active
        sheet.append(headers)
        for row in rows:
            sheet.append(row)
        stream = io.BytesIO()
        workbook.save(stream)
        return base64.b64encode(stream.getvalue())

    def _quantitative_row(self, min_value=120, max_value=130, uom_name=None):
        return [
            "PCB Name",
            "Operating Temperature",
            "quantitative",
            "Target range 120-130 C",
            "",
            "",
            min_value,
            max_value,
            uom_name or self.unit_uom.name,
        ]

    def _qualitative_row(self, value_name, ok):
        return [
            "PCB Name",
            "Visual Inspection",
            "qualitative",
            "Inspect the PCB surface",
            value_name,
            "TRUE" if ok else "FALSE",
            "",
            "",
            "",
        ]

    def test_import_and_update_excel(self):
        data_file = self._build_workbook(
            [
                self._quantitative_row(),
                self._qualitative_row("OK", True),
                self._qualitative_row("Needs Rework", False),
            ]
        )
        load_result = self.loader.load_from_binary(data_file, "import.xlsx")
        self.assertFalse(load_result["errors"])
        self.assertEqual(len(load_result["rows"]), 3)

        summary = self.loader.import_rows(load_result["rows"], "create_update")
        self.assertEqual(summary["tests_created"], 1)
        self.assertEqual(summary["triggers_created"], 0)
        self.assertEqual(summary["questions_created"], 2)
        self.assertEqual(summary["values_created"], 2)

        test = self.env["qc.test"].search([("name", "=", "PCB Name")], limit=1)
        self.assertTrue(test)
        self.assertEqual(test.code, "PCB_NAME")
        self.assertFalse(test.fill_correct_values)
        self.assertEqual(test.type, "generic")

        quantitative = test.test_lines.filtered(lambda q: q.name == "Operating Temperature")
        self.assertEqual(quantitative.type, "quantitative")
        self.assertEqual(quantitative.min_value, 120.0)
        self.assertEqual(quantitative.max_value, 130.0)
        self.assertEqual(quantitative.uom_id, self.unit_uom)

        qualitative = test.test_lines.filtered(lambda q: q.name == "Visual Inspection")
        self.assertEqual(len(qualitative.ql_values), 2)
        ok_values = qualitative.ql_values.filtered("ok")
        self.assertEqual(ok_values.mapped("name"), ["OK"])
        self.assertIn("Needs Rework", qualitative.ql_values.mapped("name"))

        # Update workbook: adjust limits, change fill flag, keep only one qualitative value
        updated_file = self._build_workbook(
            [
                self._quantitative_row(min_value=121, max_value=132),
                self._qualitative_row("OK", True),
            ]
        )
        updated_result = self.loader.load_from_binary(updated_file, "import.xlsx")
        self.assertFalse(updated_result["errors"])
        summary_update = self.loader.import_rows(
            updated_result["rows"], "create_update"
        )
        self.assertEqual(summary_update["tests_updated"], 1)
        self.assertEqual(summary_update["questions_updated"], 2)
        self.assertEqual(summary_update["values_deleted"], 1)
        self.assertEqual(summary_update["triggers_updated"], 0)

        test = self.env["qc.test"].browse(test.id)
        quantitative = self.env["qc.test.question"].browse(quantitative.id)
        qualitative = self.env["qc.test.question"].browse(qualitative.id)
        self.assertEqual(quantitative.min_value, 121.0)
        self.assertEqual(quantitative.max_value, 132.0)
        self.assertEqual(qualitative.ql_values.mapped("name"), ["OK"])

    def test_autoselect_ok_value_when_missing(self):
        data_file = self._build_workbook(
            [
                self._qualitative_row("Needs Rework", False),
            ]
        )
        load_result = self.loader.load_from_binary(data_file, "missing_ok.xlsx")
        self.assertFalse(load_result["errors"])
        summary = self.loader.import_rows(load_result["rows"], "create_update")
        self.assertEqual(summary["tests_created"], 1)

        test = self.env["qc.test"].search([("name", "=", "PCB Name")], limit=1)
        self.assertTrue(test)
        question = test.test_lines.filtered(lambda q: q.name == "Visual Inspection")
        self.assertTrue(question)
        self.assertEqual(len(question.ql_values), 1)
        value = question.ql_values[0]
        self.assertEqual(value.name, "Needs Rework")
        self.assertTrue(value.ok)
