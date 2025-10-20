# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import json

from odoo import _, fields, models
from odoo.exceptions import UserError


class QcImportExcelWizard(models.TransientModel):
    _name = "qc.import.excel.wizard"
    _description = "Import quality tests from Excel"

    import_mode = fields.Selection(
        selection=[
            ("create", "Yalnızca yeni test oluştur"),
            ("update", "Mevcutları güncelle"),
            ("create_update", "Yeni test oluştur ve mevcutları güncelle"),
        ],
        default="create",
        required=True,
        string="Import Mode",
    )
    data_file = fields.Binary(string="Excel File", required=True)
    filename = fields.Char(string="Filename")
    preview_line_ids = fields.One2many(
        comodel_name="qc.import.excel.preview",
        inverse_name="wizard_id",
        string="Preview Lines",
        readonly=True,
    )

    def _open_self_action(self):
        return {
            "type": "ir.actions.act_window",
            "name": _("Import Quality Tests"),
            "res_model": self._name,
            "view_mode": "form",
            "res_id": self.id,
            "target": "new",
        }

    def action_preview(self):
        self.ensure_one()
        loader = self.env["qc.excel.loader"]
        load_result = loader.load_from_binary(self.data_file, self.filename)
        if load_result["errors"]:
            raise UserError(loader.format_errors(load_result["errors"]))
        rows = load_result.get("rows") or []
        if not rows:
            raise UserError(
                _(
                    "The uploaded template does not contain any data rows. "
                    "Please verify the content before retrying."
                )
            )

        if self.preview_line_ids:
            self.preview_line_ids.unlink()

        preview_model = self.env["qc.import.excel.preview"]
        preview_vals_list = []
        for row in rows:
            data = row["data"]
            raw = row["raw"]
            preview_vals_list.append(
                {
                    "wizard_id": self.id,
                    "row_index": row["row_index"],
                    "product_template_default_code": self._get_product_code(
                        data, raw
                    ),
                    "test_code": data.get("test_code"),
                    "test_name": data.get("test_name"),
                    "trigger_name": data.get("trigger_name"),
                    "trigger_timing": data.get("trigger_timing"),
                    "question_code": data.get("question_code"),
                    "question_name": data.get("question_name"),
                    "question_type": data.get("question_type"),
                    "uom_xmlid": self._get_uom_xmlid(data, raw),
                    "min_value": self._format_number(data.get("min_value")),
                    "max_value": self._format_number(data.get("max_value")),
                    "fill_correct_values": data.get("fill_correct_values", False),
                    "qualitative_value_name": data.get("qualitative_value_name"),
                    "qualitative_value_ok": data.get("qualitative_value_ok", False),
                    "raw_payload": json.dumps(raw, ensure_ascii=False, sort_keys=True),
                }
            )
        preview_model.create(preview_vals_list)
        return self._open_self_action()

    def action_import(self):
        self.ensure_one()
        loader = self.env["qc.excel.loader"]
        load_result = loader.load_from_binary(self.data_file, self.filename)
        if load_result["errors"]:
            raise UserError(loader.format_errors(load_result["errors"]))
        rows = load_result.get("rows") or []
        if not rows:
            raise UserError(
                _(
                    "The uploaded template does not contain any data rows. "
                    "Please verify the content before retrying."
                )
            )
        summary = loader.import_rows(rows, self.import_mode)
        message = self._format_summary(summary)
        action = self._open_self_action()
        notifier = getattr(self.env.user, "notify_success", None)
        if callable(notifier):
            notifier(message=message)
        else:
            action.setdefault(
                "effect",
                {
                    "fadeout": "slow",
                    "message": message,
                    "type": "rainbow_man",
                },
            )
        return action

    def _get_product_code(self, data, raw):
        product = data.get("product_template")
        if product:
            return product.default_code
        return raw.get(
            "trigger_product_template_line_ids/product_template/default_code"
        )

    def _get_uom_xmlid(self, data, raw):
        uom = data.get("uom_id")
        if not uom:
            return raw.get("test_lines/uom_id/id")
        xmlids = uom.get_external_id()
        return xmlids.get(uom.id) or raw.get("test_lines/uom_id/id")

    def _format_number(self, value):
        if value in (None, ""):
            return ""
        return str(value)

    def _format_summary(self, summary):
        return _(
            "Tests created: %(tests_created)d, updated: %(tests_updated)d. "
            "Questions created: %(questions_created)d, updated: %(questions_updated)d, "
            "deleted: %(questions_deleted)d. "
            "Values created: %(values_created)d, updated: %(values_updated)d, "
            "deleted: %(values_deleted)d. "
            "Trigger lines created: %(triggers_created)d, updated: %(triggers_updated)d."
        ) % summary


class QcImportExcelPreview(models.TransientModel):
    _name = "qc.import.excel.preview"
    _description = "Preview rows generated from the QC Excel template"
    _order = "row_index"

    wizard_id = fields.Many2one(
        comodel_name="qc.import.excel.wizard",
        required=True,
        ondelete="cascade",
    )
    row_index = fields.Integer(string="Row")
    product_template_default_code = fields.Char(string="Product Code")
    test_code = fields.Char(string="Test Code")
    test_name = fields.Char(string="Test Name")
    trigger_name = fields.Char(string="Trigger")
    trigger_timing = fields.Char(string="Timing")
    question_code = fields.Char(string="Question Code")
    question_name = fields.Char(string="Question Name")
    question_type = fields.Char(string="Question Type")
    uom_xmlid = fields.Char(string="UoM XML-ID")
    min_value = fields.Char(string="Min")
    max_value = fields.Char(string="Max")
    fill_correct_values = fields.Boolean(string="Prefill OK Values")
    qualitative_value_name = fields.Char(string="Qualitative Value")
    qualitative_value_ok = fields.Boolean(string="Is OK?")
    raw_payload = fields.Text(string="Raw Data")
