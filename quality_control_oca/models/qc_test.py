# Copyright 2010 NaN Projectes de Programari Lliure, S.L.
# Copyright 2014 Serv. Tec. Avanzados - Pedro M. Baeza
# Copyright 2014 Oihane Crucelaegui - AvanzOSC
# Copyright 2017 ForgeFlow S.L.
# Copyright 2017 Simone Rubino - Agile Business Group
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import _, api, exceptions, fields, models


class QcTest(models.Model):
    """
    A test is a group of questions along with the values that make them valid.
    """

    _name = "qc.test"
    _description = "Quality control test"
    _inherit = "mail.thread"

    def object_selection_values(self):
        return set()

    @api.onchange("type")
    def onchange_type(self):
        if self.type == "generic":
            self.object_id = False

    active = fields.Boolean(default=True)
    code = fields.Char(index=True, help="Unique identifier used for imports and integrations.")
    name = fields.Char(required=True, translate=True)
    test_lines = fields.One2many(
        comodel_name="qc.test.question",
        inverse_name="test",
        string="Questions",
        copy=True,
    )
    trigger_product_template_line_ids = fields.One2many(
        comodel_name="qc.trigger.product_template_line",
        inverse_name="test",
        string="Product Template Trigger Lines",
    )
    object_id = fields.Reference(
        string="Reference object",
        selection="object_selection_values",
    )
    fill_correct_values = fields.Boolean(string="Pre-fill with correct values")
    type = fields.Selection(
        [("generic", "Generic"), ("related", "Related")],
        required=True,
        default="generic",
    )
    category = fields.Many2one(comodel_name="qc.test.category")
    company_id = fields.Many2one(
        comodel_name="res.company",
        default=lambda self: self.env.company,
    )

    @api.model
    def action_open_export_wizard(self):
        """Open the export wizard without requiring XML-ID resolution at load."""

        action = self.env["ir.actions.actions"]._for_xml_id(
            "quality_control_oca.action_qc_export_excel_wizard"
        )
        context = dict(self.env.context)
        active_ids = context.get("active_ids") or self.ids
        if not isinstance(active_ids, list):
            active_ids = [active_ids]
        context.update(
            {
                "active_model": "qc.test",
                "active_ids": active_ids,
                "active_id": active_ids[0] if active_ids else False,
                "default_test_ids": [(6, 0, active_ids)],
            }
        )
        action["context"] = context
        return action

    @api.model
    def action_open_import_wizard(self):
        """Open the custom Excel import wizard."""

        action = self.env["ir.actions.actions"]._for_xml_id(
            "quality_control_oca.action_qc_import_excel_wizard"
        )
        action_context = dict(self.env.context)
        action["context"] = action_context
        return action

    @api.model
    def get_import_templates(self):
        """Expose the Excel template both in the wizard and generic importer."""

        templates = list(super().get_import_templates())
        template_url = "/quality_control_oca/static/xlsx/qc_product_questions_template.xlsx"
        if not any(template.get("template") == template_url for template in templates):
            templates.append(
                {
                    "label": _("Quality tests Excel template"),
                    "template": template_url,
                }
            )
        return templates

    def _auto_init(self):
        """Ensure legacy databases get the new ``code`` column and index."""

        # Call super first so the base table exists on fresh installations.
        res = super()._auto_init()
        self._cr.execute(
            'ALTER TABLE "%s" ADD COLUMN IF NOT EXISTS "code" varchar'
            % self._table
        )
        self._cr.execute(
            'CREATE INDEX IF NOT EXISTS "%s_code_index" ON "%s" ("code")'
            % (self._table, self._table)
        )
        return res


class QcTestQuestion(models.Model):
    """Each test line is a question with its valid value(s)."""

    _name = "qc.test.question"
    _description = "Quality control question"
    _order = "sequence, id"

    def create(self, vals_list):
        questions = super().create(vals_list)
        questions._ensure_ok_answer()
        return questions

    def write(self, vals):
        res = super().write(vals)
        self._ensure_ok_answer()
        return res

    @api.constrains("ql_values")
    def _check_valid_answers(self):
        for tc in self:
            if (
                tc.type == "qualitative"
                and tc.ql_values
                and not tc.ql_values.filtered("ok")
            ):
                answers = ", ".join(tc.ql_values.mapped("name")) or "-"
                raise exceptions.ValidationError(
                    self.env._(
                        "Question '%(question)s' is not valid: you have to mark at least one value as OK. "
                        "Tick the field \"Qualitative values / Correct answer?\" (Excel column "
                        "\"test_lines/ql_values/ok\") for one of the answers. Current answers: %(answers)s"
                    )
                    % {"question": tc.display_name, "answers": answers}
                )

    def _ensure_ok_answer(self):
        for question in self:
            if (
                question.type == "qualitative"
                and question.ql_values
                and not question.ql_values.filtered("ok")
            ):
                question.ql_values[0].write({"ok": True})

    @api.constrains("min_value", "max_value")
    def _check_valid_range(self):
        for tc in self:
            if tc.type == "quantitative" and tc.min_value > tc.max_value:
                raise exceptions.ValidationError(
                    self.env._(
                        "Question '%s' is not valid: "
                        "minimum value can't be higher than maximum value."
                    )
                    % tc.display_name
                )

    sequence = fields.Integer(required=True, default="10")
    code = fields.Char(index=True, help="Unique identifier used for imports and integrations.")
    test = fields.Many2one(comodel_name="qc.test")
    name = fields.Char(required=True, translate=True)
    type = fields.Selection(
        [("qualitative", "Qualitative"), ("quantitative", "Quantitative")],
        required=True,
    )
    ql_values = fields.One2many(
        comodel_name="qc.test.question.value",
        inverse_name="test_line",
        string="Qualitative values",
        copy=True,
    )
    notes = fields.Text()
    min_value = fields.Float(string="Min", digits="Quality Control")
    max_value = fields.Float(string="Max", digits="Quality Control")
    uom_id = fields.Many2one(comodel_name="uom.uom", string="Uom")

    def _auto_init(self):
        """Ensure legacy databases get the new ``code`` column and index."""

        res = super()._auto_init()
        self._cr.execute(
            'ALTER TABLE "%s" ADD COLUMN IF NOT EXISTS "code" varchar'
            % self._table
        )
        self._cr.execute(
            'CREATE INDEX IF NOT EXISTS "%s_code_index" ON "%s" ("code")'
            % (self._table, self._table)
        )
        return res


class QcTestQuestionValue(models.Model):
    _name = "qc.test.question.value"
    _description = "Possible values for qualitative questions."

    test_line = fields.Many2one(comodel_name="qc.test.question", string="Test question")
    name = fields.Char(required=True, translate=True)
    ok = fields.Boolean(
        string="Correct answer?",
        help="When this field is marked, the answer is considered correct.",
    )
