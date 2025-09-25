"""Excel import/export helpers for quality control tests."""

import base64
import os

from odoo import api, models
from odoo.exceptions import UserError


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
    def import_from_excel(self, file_path):
        """Create or update tests from an Excel ``file_path`` using the loader."""

        loader = self.env["qc.excel.loader"]
        try:
            with open(file_path, "rb") as stream:
                encoded = base64.b64encode(stream.read())
        except OSError as exc:
            raise UserError(
                self.env._(
                    "The Excel file %(path)s could not be read: %(error)s"
                )
                % {"path": file_path, "error": exc}
            ) from exc

        load_result = loader.load_from_binary(encoded, os.path.basename(file_path))
        if load_result["errors"]:
            raise UserError(loader.format_errors(load_result["errors"]))

        loader.import_rows(load_result["rows"], "create_update")
        return self
