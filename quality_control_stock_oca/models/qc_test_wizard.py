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
        tests = self.env["qc.test"].browse(self.env.context.get("active_ids", []))
        with NamedTemporaryFile(suffix=".xlsx") as tmp:
            tests.export_to_excel(tmp.name)
            tmp.seek(0)
            self.file_data = base64.b64encode(tmp.read())
        return {
            "type": "ir.actions.act_url",
            "url": (
                f"/web/content/?model={self._name}&id={self.id}&field=file_data"
                f"&download=true&filename={self.file_name}"
            ),
            "target": "self",
        }


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
