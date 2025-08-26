"""Excel import/export helpers for quality control tests."""

from io import BytesIO

from openpyxl import Workbook, load_workbook

from odoo import api, models


class QcTest(models.Model):
    """Extend ``qc.test`` with Excel export/import utilities.

    These helpers allow bulk creation or update of quality control tests
    using simple Excel files, which is convenient when many tests need to be
    managed outside the Odoo UI.
    """

    _inherit = "qc.test"

    @api.model
    def _excel_fields(self):
        """Return a list of fields to export/import.

        The list is intentionally small and only includes basic attributes that
        are available in all databases.  It can be extended by inheriting
        modules if needed.
        """

        return ["name", "active"]

    def export_to_excel(self, file_path):
        """Export the current recordset to ``file_path``.

        ``file_path`` must be a writable file location.  The exported workbook
        will contain one sheet with a header row followed by the values of each
        record.
        """

        wb = Workbook()
        ws = wb.active
        fields = self._excel_fields()
        ws.append(fields)
        for test in self:
            ws.append([getattr(test, field) for field in fields])
        wb.save(file_path)

    @api.model
    def import_from_excel(self, file_path):
        """Create tests from the spreadsheet located at ``file_path``.

        The first row of the sheet must contain the field names matching those
        returned by :meth:`_excel_fields`.  Subsequent rows are imported as
        new records.
        """

        with open(file_path, "rb") as f:
            wb = load_workbook(filename=BytesIO(f.read()))
        ws = wb.active
        rows = list(ws.iter_rows(values_only=True))
        if not rows:
            return self
        headers = [str(h) for h in rows[0]]
        for row in rows[1:]:
            values = dict(zip(headers, row, strict=False))
            # Filter out empty keys that may appear if columns are left blank
            values = {k: v for k, v in values.items() if k}
            self.create(values)
        return self
