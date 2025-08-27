"""Excel import/export helpers for quality control tests."""

from io import BytesIO

from openpyxl import Workbook, load_workbook

from odoo import api, models


class QcTest(models.Model):
    """Extend ``qc.test`` with Excel export/import utilities.

    These helpers allow bulk creation or update of quality control tests using
    simple Excel files, including their question lines.
    """

    _inherit = "qc.test"

    @api.model
    def _excel_fields(self):
        """Return a list of fields to export/import for tests."""

        return ["name", "active"]

    @api.model
    def _question_field(self):
        """Return the one2many field name that holds test questions.

        Different quality-control modules have renamed this relation over
        time.  The helper looks for a known field and falls back to
        ``question_ids``.
        """

        for name in ("question_ids", "test_lines", "test_line_ids"):
            if name in self._fields:
                return name
        return "question_ids"

    @api.model
    def _qualitative_field(self):
        """Return the field holding allowed values on questions if any."""

        Question = self.env["qc.test.question"]
        for name, field in Question._fields.items():
            if field.type in ("many2many", "many2one") and "value" in name:
                return name
        return None

    def export_to_excel(self, file_path):
        """Export tests and their questions to ``file_path``.

        The workbook contains two sheets:

        * ``tests`` – fields returned by :meth:`_excel_fields`
        * ``questions`` – each question linked to its test by name
        """

        wb = Workbook()
        ws_tests = wb.active
        ws_tests.title = "tests"
        fields = self._excel_fields()
        ws_tests.append(fields)
        for test in self:
            ws_tests.append([getattr(test, field) for field in fields])

        ws_questions = wb.create_sheet("questions")
        qual_field = self._qualitative_field()
        headers = [
            "test_name",
            "name",
            "type",
            "min_value",
            "max_value",
            "uom_id/id",
            "sequence",
            "notes",
        ]
        if qual_field:
            headers.append(f"{qual_field}/name")
        ws_questions.append(headers)

        q_field = self._question_field()
        for test in self:
            for question in getattr(test, q_field, []):
                row = [
                    test.name,
                    getattr(question, "name", ""),
                    getattr(question, "type", ""),
                    getattr(question, "min_value", ""),
                    getattr(question, "max_value", ""),
                    getattr(question, "uom_id", False) and question.uom_id.id or "",
                    getattr(question, "sequence", ""),
                    getattr(question, "notes", ""),
                ]
                if qual_field:
                    value = getattr(question, qual_field)
                    names = value.mapped("name") if value else []
                    row.append(",".join(names))
                ws_questions.append(row)

        wb.save(file_path)

    @api.model
    def import_from_excel(self, file_path):
        """Create tests and questions from ``file_path``."""

        with open(file_path, "rb") as f:
            wb = load_workbook(filename=BytesIO(f.read()))
        ws = wb.active
        rows = list(ws.iter_rows(values_only=True))
        if not rows:
            return self
        headers = [str(h) for h in rows[0]]
        tests = {}
        for row in rows[1:]:
            values = dict(zip(headers, row, strict=False))
            values = {k: v for k, v in values.items() if k}
            test = self.create(values)
            tests[test.name] = test
        q_field = self._question_field()
        qual_field = self._qualitative_field()
        Question = self.env["qc.test.question"]
        qual_type = qual_field and Question._fields[qual_field].type or None
        if "questions" in wb.sheetnames:
            q_rows = list(wb["questions"].iter_rows(values_only=True))
            if q_rows:
                q_headers = [str(h) for h in q_rows[0]]
                for row in q_rows[1:]:
                    q_vals = dict(zip(q_headers, row, strict=False))
                    test_name = q_vals.get("test_name")
                    if test_name and test_name in tests:
                        vals = {
                            "name": q_vals.get("name"),
                            "type": q_vals.get("type"),
                            "min_value": q_vals.get("min_value"),
                            "max_value": q_vals.get("max_value"),
                            "sequence": q_vals.get("sequence"),
                            "notes": q_vals.get("notes"),
                        }
                        uom = q_vals.get("uom_id/id")
                        if uom:
                            try:
                                vals["uom_id"] = int(uom)
                            except (ValueError, TypeError):
                                vals["uom_id"] = False
                        if qual_field:
                            qual = q_vals.get(f"{qual_field}/name")
                            if qual:
                                names = [x.strip() for x in str(qual).split(",") if x]
                                rel_model = Question._fields[qual_field].comodel_name
                                records = self.env[rel_model].search(
                                    [("name", "in", names)]
                                )
                                if qual_type == "many2many":
                                    vals[qual_field] = [(6, 0, records.ids)]
                                elif qual_type == "many2one":
                                    vals[qual_field] = (
                                        records[:1].id if records else False
                                    )
                        if vals.get("name"):
                            tests[test_name].write({q_field: [(0, 0, vals)]})
        return self
