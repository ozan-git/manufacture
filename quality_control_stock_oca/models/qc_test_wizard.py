import base64
from tempfile import NamedTemporaryFile

from odoo import fields, models


class QcTestExportWizard(models.TransientModel):
    """Wizard to export quality control tests to Excel."""

    _name = "qc.test.export.wizard"
    _description = "QC Test Excel Export"

    file_data = fields.Binary("File", readonly=True)
    file_name = fields.Char(readonly=True, default="qc_tests.xlsx")

    def action_export(self):
        self.ensure_one()
        context = dict(self.env.context)
        active_ids = context.get("active_ids")
        if not active_ids and context.get("active_id"):
            active_ids = [context["active_id"]]
        wizard_ctx = dict(context, active_ids=active_ids, active_model="qc.test")
        export_wizard = (
            self.env["qc.export.excel.wizard"].with_context(wizard_ctx).create({})
        )
        action = export_wizard.action_export()
        self.write(
            {
                "file_data": export_wizard.data_file,
                "file_name": export_wizard.filename or self.file_name,
            }
        )
        return action


class QcTestImportWizard(models.TransientModel):
    """Wizard to import quality control tests from Excel."""

    _name = "qc.test.import.wizard"
    _description = "QC Test Excel Import"

    file_data = fields.Binary("File", required=True)
    file_name = fields.Char()

    def action_import(self):
        self.ensure_one()
        data = base64.b64decode(self.file_data or b"")
        with NamedTemporaryFile(suffix=".xlsx") as tmp:
            tmp.write(data)
            tmp.flush()
            self.env["qc.test"].import_from_excel(tmp.name)
        return {"type": "ir.actions.act_window_close"}
