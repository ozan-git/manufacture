"""Excel import/export helpers for quality control tests."""

import base64
from collections import defaultdict

from openpyxl import load_workbook

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
        for name, field in Question._fields.items():
            if field.type == "one2many" and "value" in name:
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
        """Export tests to ``file_path`` using the shared template wizard."""

        wizard = (
            self.env["qc.export.excel.wizard"].with_context(
                active_ids=self.ids, active_model="qc.test"
            )
        ).create({})
        wizard.action_export()
        if not wizard.data_file:
            return
        with open(file_path, "wb") as output:
            output.write(base64.b64decode(wizard.data_file))

    @api.model
    def import_from_excel(self, file_path):  # noqa: C901
        """Create tests and questions from ``file_path``."""

        workbook = load_workbook(filename=file_path)
        try:
            sheet = workbook.active
            rows = list(sheet.iter_rows(values_only=True))
        finally:
            workbook.close()
        if not rows:
            return self

        headers = [str(header or "").strip() for header in rows[0]]
        header_index = {name: index for index, name in enumerate(headers) if name}
        if not header_index:
            return self

        def get_value(container, *names):
            for name in names:
                if name in container and container[name] not in (None, ""):
                    return container[name]
            for name in names:
                if name in container:
                    return container[name]
            return None

        q_field = self._question_field()
        q_field_def = self._fields[q_field]
        question_model = self.env[q_field_def.comodel_name]
        question_inverse = q_field_def.inverse_name

        qual_field = self._qualitative_field()
        value_model = None
        value_inverse = None
        qual_field_def = None
        if qual_field and qual_field in question_model._fields:
            qual_field_def = question_model._fields[qual_field]
            if qual_field_def.type == "one2many":
                value_model = self.env[qual_field_def.comodel_name]
                value_inverse = qual_field_def.inverse_name

        tests = {}
        questions = {}
        created_values = defaultdict(set)

        def to_bool(value):
            if isinstance(value, bool):
                return value
            if isinstance(value, str):
                return value.strip().lower() in {"1", "true", "yes", "y"}
            if isinstance(value, (int, float)):
                return bool(value)
            return False

        def to_float(value):
            if value in (None, ""):
                return None
            if isinstance(value, (int, float)):
                return float(value)
            try:
                return float(str(value))
            except (TypeError, ValueError):
                return None

        def resolve_xmlid(xmlid):
            if not xmlid:
                return None
            try:
                return self.env.ref(str(xmlid))
            except (ValueError, TypeError):
                return None

        for raw in rows[1:]:
            if not raw or not any(raw):
                continue

            data = {
                name: raw[index] if index < len(raw) else None
                for name, index in header_index.items()
            }

            test_key = get_value(data, "code", "test_code") or get_value(
                data, "name", "test_name"
            )
            if not test_key:
                continue

            test = tests.get(test_key)
            if not test:
                category = resolve_xmlid(get_value(data, "category/id", "test_category_xmlid"))
                test_type = get_value(data, "type", "test_type") or "generic"
                if isinstance(test_type, str):
                    test_type = test_type.strip() or "generic"
                test_vals = {
                    "name": get_value(data, "name", "test_name") or test_key,
                    "code": get_value(data, "code", "test_code") or False,
                    "type": test_type,
                    "fill_correct_values": to_bool(data.get("fill_correct_values")),
                }
                if category:
                    test_vals["category"] = category.id
                test = self.create(test_vals)
                tests[test_key] = test

            question_code = get_value(data, "test_lines/code", "question_code") or ""
            question_name = get_value(data, "test_lines/name", "question_name") or ""
            question_sequence = (
                get_value(data, "test_lines/sequence", "question_sequence") or 0
            )
            question_key = (
                test.id,
                question_code,
                question_name,
                question_sequence,
            )

            question = questions.get(question_key)
            if not question:
                q_type = get_value(data, "test_lines/type", "question_type") or "qualitative"
                if isinstance(q_type, str):
                    q_type = q_type.strip().lower() or "qualitative"
                q_vals = {
                    question_inverse: test.id,
                    "name": question_name or question_code or "Question",
                    "type": q_type,
                }
                if question_code:
                    q_vals["code"] = question_code
                notes = get_value(data, "test_lines/notes", "question_notes")
                if notes not in (None, ""):
                    q_vals["notes"] = notes
                if question_sequence not in (None, ""):
                    try:
                        q_vals["sequence"] = int(question_sequence)
                    except (TypeError, ValueError):
                        q_vals["sequence"] = 0
                if q_type == "quantitative":
                    min_value = to_float(
                        get_value(data, "test_lines/min_value", "min_value")
                    )
                    max_value = to_float(
                        get_value(data, "test_lines/max_value", "max_value")
                    )
                    if min_value is not None:
                        q_vals["min_value"] = min_value
                    if max_value is not None:
                        q_vals["max_value"] = max_value
                    uom = resolve_xmlid(get_value(data, "test_lines/uom_id/id", "uom_xmlid"))
                    if uom:
                        q_vals["uom_id"] = uom.id
                question = question_model.create(q_vals)
                questions[question_key] = question
            else:
                q_type = question.type

            if value_model and q_type == "qualitative" and value_inverse:
                value_name = get_value(
                    data, "test_lines/ql_values/name", "qualitative_value_name"
                )
                if value_name:
                    value_ok = to_bool(
                        get_value(
                            data,
                            "test_lines/ql_values/ok",
                            "qualitative_value_ok",
                        )
                    )
                    value_key = (value_name, value_ok)
                    if value_key in created_values[question.id]:
                        continue
                    value_vals = {value_inverse: question.id, "name": value_name}
                    if "ok" in value_model._fields:
                        value_vals["ok"] = value_ok
                    value_model.create(value_vals)
                    created_values[question.id].add(value_key)

        return self
