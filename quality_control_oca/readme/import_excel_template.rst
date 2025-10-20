Excel Template For QC Tests
===========================

.. download:: ../static/xlsx/qc_product_questions_template.xlsx
   :description: Download the latest QC product test template
   :filename: qc_product_questions_template.xlsx

Purpose
-------

The spreadsheet focuses on the details you can enter while designing a test:
its name, the questions that should appear on inspections, and the possible
answers. Technical fields such as internal codes, triggers, or categories are
now handled automatically by the importer so that you only have to maintain the
content that matters for the shop floor.

Downloading The Template
------------------------

You can always grab the latest version of the spreadsheet from the
``Import Tests from Excel`` wizard. Click *Download template* to retrieve the
file alongside the static link above.

Using The Template
------------------

There are two supported ways to load data prepared with this workbook:

#. In the Odoo UI, open *Quality Control → Tests* and use the *Import from
   Excel* button. The same wizard is also available from *Actions ▸ Import
   Tests from Excel* in the list view toolbar. Both entries show a link to download
   this template. The dedicated wizard validates the file, shows a preview, and
   applies the changes in create/update mode without extra mapping.
#. From custom scripts, call ``env['qc.test'].import_from_excel('/path/to/file.xlsx')``.
   The helper reuses the same loader as the wizard, so every path accepts the
   exact same headers and validations. Legacy column names from older versions
   are still recognized.

The generic import action available from list views is not aware of the nested
column names used by this template. Stick to the dedicated wizard or helper
above to avoid field-mapping issues.

Exporting Existing Tests
------------------------

Open *Quality Control → Tests*, select the records you want, and use the
*Export to Excel* button (or the *Actions ▸ Export Tests to Excel* entry).
The generated workbook mirrors the import template, so you can tweak the data
and re-import it without changing column names.

Template Columns
----------------

.. list-table:: QC Excel columns
   :header-rows: 1
   :widths: 22 10 20 38 20

   * - Column
     - Required
     - Accepted values
     - Description
     - Example
   * - ``name``
     - Required
     - Text
     - Display name of the quality test.
     - ``PCB Name``
   * - ``test_lines/name``
     - Required
     - Text
     - Label shown on the inspection line.
     - ``Operating Temperature``
   * - ``test_lines/type``
     - Optional
     - ``qualitative`` | ``quantitative``
     - Defaults to ``qualitative`` when left empty. Use ``quantitative`` for
       numeric checks.
     - ``qualitative``
   * - ``test_lines/notes``
     - Optional
     - Text
     - Additional instructions displayed on the inspection line.
     - ``Inspect the PCB surface``
   * - ``test_lines/ql_values/name``
     - Conditional
     - Text
     - Qualitative option created under the question. Create extra rows for
       additional values.
     - ``OK``
   * - ``test_lines/ql_values/ok``
     - Conditional
     - ``TRUE`` | ``FALSE``
     - Marks the qualitative option as acceptable. At least one value should be
       ``TRUE`` whenever qualitative values are provided.
     - ``TRUE``
   * - ``test_lines/min_value``
     - Conditional
     - Number
     - Minimum accepted value for quantitative questions.
     - ``120``
   * - ``test_lines/max_value``
     - Conditional
     - Number
     - Maximum accepted value for quantitative questions.
     - ``130``
   * - ``test_lines/uom``
     - Conditional
     - Text
     - Unit of measure for quantitative questions. You can enter the display
       name (e.g. ``Units``) or an XML-ID (e.g. ``uom.product_uom_unit``).
     - ``Units``

Example Dataset
---------------

The template ships with a minimal sample showing one qualitative question
with two answers. Below is another example that mixes both question types.

.. list-table:: Sample rows
   :header-rows: 1
   :widths: 20 20 12 18 14 12 10 10

   * - Test name
     - Question
     - Type
     - Notes
     - Answer
     - OK?
     - Min
     - Max
   * - ``PCB Name``
     - ``Operating Temperature``
     - ``quantitative``
     - ``Target range 120-130 C``
     - ``-``
     - ``-``
     - ``120``
     - ``130``
   * - ``PCB Name``
     - ``Visual Inspection``
     - ``qualitative``
     - ``Inspect the PCB surface``
     - ``OK``
     - ``TRUE``
     - ``-``
     - ``-``
   * - ``PCB Name``
     - ``Visual Inspection``
     - ``qualitative``
     - ``Inspect the PCB surface``
     - ``Needs Rework``
     - ``FALSE``
     - ``-``
     - ``-``

Filling Checklist
-----------------

#. Download the template and make a copy for your project.
#. Fill in the ``name`` column for the test and add one row per question.
#. Leave ``test_lines/type`` empty for qualitative questions. Use
   ``quantitative`` when you also provide ``min_value``/``max_value``.
#. Add an extra row for every possible qualitative answer and tick ``TRUE`` in
   ``test_lines/ql_values/ok`` for the acceptable choice. If you forget to mark
   one, the importer will automatically treat the first option as the OK value.
#. For quantitative checks, provide ``test_lines/uom`` with the unit name as it
   appears in Odoo (or an XML-ID) together with the min/max values.
#. Save the file as ``.xlsx`` without changing the header names before running
   the import wizard.

.. include:: template_changelog.rst
