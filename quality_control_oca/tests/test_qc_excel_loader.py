# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import base64
import io

from odoo.tests.common import TransactionCase

try:  # pragma: no cover - optional dependency guard
    from openpyxl import Workbook
except ImportError:  # pragma: no cover - handled in tests
    Workbook = None


HEADERS = [
    "trigger_product_template_line_ids/product_template/default_code",
    "trigger_product_template_line_ids/product_template/name",
    "code",
    "name",
    "type",
    "category/id",
    "fill_correct_values",
    "trigger_product_template_line_ids/trigger/name",
    "trigger_product_template_line_ids/timing",
    "test_lines/sequence",
    "test_lines/code",
    "test_lines/name",
    "test_lines/type",
    "test_lines/notes",
    "test_lines/uom_id/id",
    "test_lines/min_value",
    "test_lines/max_value",
    "test_lines/ql_values/name",
    "test_lines/ql_values/ok",
]


class TestQcExcelLoader(TransactionCase):
    def setUp(self):
        super().setUp()
        if Workbook is None:
            self.skipTest("openpyxl is not available")
        self.loader = self.env["qc.excel.loader"]
        self.product_template = self.env["product.template"].create(
            {"name": "Sterilized Filter", "default_code": "FERT-001"}
        )

    def _build_workbook(self, rows):
        workbook = Workbook()
        sheet = workbook.active
        sheet.append(HEADERS)
        for row in rows:
            sheet.append(row)
        stream = io.BytesIO()
        workbook.save(stream)
        return base64.b64encode(stream.getvalue())

    def _quantitative_row(self, min_value=120, max_value=130, timing="after", fill=True):
        return [
            self.product_template.default_code,
            self.product_template.name,
            "STERIL_TEST",
            "Sterility Check",
            "related",
            "quality_control_oca.qc_test_category_process",
            fill,
            "Manufacturing Order",
            timing,
            10,
            "STER_TEMP",
            "Sterilization Temperature",
            "quantitative",
            "Target range 120-130 C",
            "uom.product_uom_celsius",
            min_value,
            max_value,
            "",
            "",
        ]

    def _qualitative_row(self, value_name, ok, timing="after", fill=True):
        return [
            self.product_template.default_code,
            self.product_template.name,
            "STERIL_TEST",
            "Sterility Check",
            "related",
            "quality_control_oca.qc_test_category_process",
            fill,
            "Manufacturing Order",
            timing,
            20,
            "STER_COLOR",
            "Filter Color",
            "qualitative",
            "Visual inspection",
            "",
            "",
            "",
            value_name,
            "TRUE" if ok else "FALSE",
        ]

    def test_import_and_update_excel(self):
        data_file = self._build_workbook(
            [
                self._quantitative_row(fill=True),
                self._qualitative_row("Clear", True, fill=True),
                self._qualitative_row("Amber", False, fill=True),
            ]
        )
        load_result = self.loader.load_from_binary(data_file, "import.xlsx")
        self.assertFalse(load_result["errors"])
        self.assertEqual(len(load_result["rows"]), 3)

        summary = self.loader.import_rows(load_result["rows"], "create_update")
        self.assertEqual(summary["tests_created"], 1)
        self.assertEqual(summary["triggers_created"], 1)
        self.assertEqual(summary["questions_created"], 2)
        self.assertEqual(summary["values_created"], 2)

        test = self.env["qc.test"].search([("code", "=", "STERIL_TEST")], limit=1)
        self.assertTrue(test)
        self.assertEqual(test.name, "Sterility Check")
        self.assertTrue(test.fill_correct_values)

        quantitative = test.test_lines.filtered(lambda q: q.code == "STER_TEMP")
        self.assertEqual(quantitative.type, "quantitative")
        self.assertEqual(quantitative.min_value, 120.0)
        self.assertEqual(quantitative.max_value, 130.0)
        self.assertEqual(quantitative.uom_id, self.env.ref("uom.product_uom_celsius"))

        qualitative = test.test_lines.filtered(lambda q: q.code == "STER_COLOR")
        self.assertEqual(len(qualitative.ql_values), 2)
        ok_values = qualitative.ql_values.filtered("ok")
        self.assertEqual(ok_values.mapped("name"), ["Clear"])

        trigger_line = self.env["qc.trigger.product_template_line"].search(
            [
                ("product_template", "=", self.product_template.id),
                ("test", "=", test.id),
            ],
            limit=1,
        )
        self.assertTrue(trigger_line)
        self.assertEqual(trigger_line.trigger.name, "Manufacturing Order")
        self.assertEqual(trigger_line.timing, "after")

        # Update workbook: adjust limits, change fill flag, keep only one qualitative value
        updated_file = self._build_workbook(
            [
                self._quantitative_row(min_value=121, max_value=132, timing="before", fill=False),
                self._qualitative_row("Clear", True, timing="before", fill=False),
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
        self.assertEqual(summary_update["triggers_updated"], 1)

        test = self.env["qc.test"].browse(test.id)
        self.assertFalse(test.fill_correct_values)
        quantitative = self.env["qc.test.question"].browse(quantitative.id)
        qualitative = self.env["qc.test.question"].browse(qualitative.id)
        trigger_line = self.env["qc.trigger.product_template_line"].browse(
            trigger_line.id
        )
        self.assertEqual(quantitative.min_value, 121.0)
        self.assertEqual(quantitative.max_value, 132.0)
        self.assertEqual(qualitative.ql_values.mapped("name"), ["Clear"])
        self.assertEqual(trigger_line.timing, "before")

        inspection = self.env["qc.inspection"].create(
            {
                "object_id": f"product.product,{self.product_template.product_variant_id.id}",
            }
        )
        wizard = (
            self.env["qc.inspection.set.test"].with_context(active_id=inspection.id)
        ).create({"test": test.id})
        wizard.action_create_test()
        self.assertEqual(inspection.test, test)
        self.assertEqual(len(inspection.inspection_lines), len(test.test_lines))

        trigger_lines = self.env["qc.trigger.product_template_line"].search(
            [
                ("product_template", "=", self.product_template.id),
                ("trigger", "=", trigger_line.trigger.id),
            ]
        )
        self.assertEqual(len(trigger_lines), 1)
