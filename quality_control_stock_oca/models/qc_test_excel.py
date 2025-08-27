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

    @api.model
    def _answer_field(self):
        """Return the one2many field that stores question answers, if any."""

        Question = self.env["qc.test.question"]
        for name, field in Question._fields.items():
            if field.type == "one2many" and "answer" in name:
                return name
        return None

    @api.model
    def _answer_fields(self):
        """Fields to export/import for answers."""

        q_ans_field = self._answer_field()
        if not q_ans_field:
            return []
        Question = self.env["qc.test.question"]
        AnswerModel = self.env[Question._fields[q_ans_field].comodel_name]
        fields = ["name"]
        for extra in ("sequence", "notes"):
            if extra in AnswerModel._fields:
                fields.append(extra)
        return fields

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

        ans_field = self._answer_field()
        ans_fields = self._answer_fields()

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

        if ans_field and ans_fields:
            ws_answers = wb.create_sheet("answers")
            ws_answers.append(["test_name", "question_name", *ans_fields])
            for test in self:
                for question in getattr(test, q_field, []):
                    for answer in getattr(question, ans_field, []):
                        ws_answers.append(
                            [
                                test.name,
                                getattr(question, "name", ""),
                                *[getattr(answer, f, "") for f in ans_fields],
                            ]
                        )

        wb.save(file_path)

    @api.model
    def import_from_excel(self, file_path):  # noqa: C901
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
        ans_field = self._answer_field()
        ans_fields = self._answer_fields()
        Answer = None
        if ans_field:
            Answer = self.env[Question._fields[ans_field].comodel_name]
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
                        question = None
                        if vals.get("name"):
                            tests[test_name].write({q_field: [(0, 0, vals)]})
                            question = getattr(tests[test_name], q_field)[-1]
                        if question and ans_field and ans_fields:
                            # store name for lookup when importing answers
                            question._import_name = q_vals.get("name")
        if ans_field and "answers" in wb.sheetnames:
            a_rows = list(wb["answers"].iter_rows(values_only=True))
            if a_rows:
                a_headers = [str(h) for h in a_rows[0]]
                rel_field = None
                for fname, field in Answer._fields.items():
                    if (
                        field.type == "many2one"
                        and field.comodel_name == Question._name
                    ):
                        rel_field = fname
                        break
                for row in a_rows[1:]:
                    a_vals = dict(zip(a_headers, row, strict=False))
                    test_name = a_vals.get("test_name")
                    q_name = a_vals.get("question_name")
                    if test_name in tests:
                        test = tests[test_name]
                        question = getattr(test, q_field).filtered(
                            lambda q, q_name=q_name: getattr(q, "_import_name", q.name)
                            == q_name
                        )[:1]
                        if question:
                            vals = {f: a_vals.get(f) for f in ans_fields}
                            if rel_field:
                                vals[rel_field] = question.id
                            Answer.create(vals)
        return self
