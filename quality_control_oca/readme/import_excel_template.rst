Excel Template For QC Tests
===========================

.. download:: ../static/xlsx/qc_product_questions_template.xlsx
   :description: Download the latest QC product test template
   :filename: qc_product_questions_template.xlsx

Purpose
-------

The Excel template helps you prepare quality control tests, their questions,
possible qualitative answers, and product triggers in a single spreadsheet.
Each row captures one question (and optionally one qualitative value) that will
be imported into ``qc.test``, ``qc.test.question`` and
``qc.test.question.value`` records and linked to product template triggers
through ``qc.trigger.product_template_line``.

Downloading The Template
------------------------

You can always grab the latest version of the spreadsheet from the
``Import Tests from Excel`` wizard. Click *Download template* to retrieve the
file alongside the static link above.

Using The Template
------------------

There are two supported ways to load data prepared with this workbook:

#. In the Odoo UI, open *Quality Control → Tests* and use the *Import from
   Excel* button (or the generic *Import* action). Both show a link to download
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
   :widths: 22 10 16 42 20

   * - Column
     - Required
     - Accepted values
     - Description
     - Example
   * - ``trigger_product_template_line_ids/product_template/default_code``
     - Optional
     - Text
     - Internal reference of the product template used to bind the trigger.
       Leave empty to keep the test generic.
     - ``FERT-001``
   * - ``trigger_product_template_line_ids/product_template/name``
     - Optional
     - Text
     - Human-readable product template name; used for review only.
     - ``Sterilized Filter``
   * - ``code``
     - Optional
     - Text (unique per test)
     - Stable identifier used to create or update the related ``qc.test``. Leave it
       empty to rely on the test name.
     - ``STERIL_TEST``
   * - ``name``
     - Required
     - Text
     - Display name of the quality test.
     - ``Sterility Check``
   * - ``type``
     - Optional
     - ``generic`` | ``related``
     - Determines whether the test is generic or linked to a specific model. Defaults
       to ``generic`` when left empty.
     - ``related``
   * - ``category/id``
     - Optional
     - Module XML-ID
     - Reference to an existing ``qc.test.category`` record (``module.record``). Provide
       this when the category has a stable external identifier.
     - ``quality_control_oca.qc_test_category_process`` (provided by this module)
   * - ``category/name``
     - Optional
     - Text
     - Category name (or full path such as ``Parent / Child``). Used as a fallback when
       no external ID is available in the previous column.
     - ``Process``
   * - ``fill_correct_values``
     - Optional
     - ``TRUE`` | ``FALSE``
     - Pre-fill inspection lines with the "OK" values when the inspection is created.
     - ``TRUE``
   * - ``trigger_product_template_line_ids/trigger/name``
     - Optional
     - Text
     - Name of the ``qc.trigger`` to use when creating the
       ``qc.trigger.product_template_line``.
     - ``Manufacturing Order`` (default trigger provided by this module)
   * - ``trigger_product_template_line_ids/timing``
     - Optional
     - ``before`` | ``after`` | ``plan_ahead``
     - Timing applied to the trigger line when the product template is filled.
     - ``after``
   * - ``test_lines/sequence``
     - Optional
     - Integer
     - Sequence used to order the questions within the test. Missing values are
       auto-generated in steps of 10 following the row order.
     - ``10``
   * - ``test_lines/code``
     - Optional
     - Text (unique per test)
     - Identifier to help detect and update existing questions. Leave empty to use
       the question name.
     - ``STER_TEMP``
   * - ``test_lines/name``
     - Required
     - Text
     - Label shown on the inspection line.
     - ``Sterilization Temperature``
   * - ``test_lines/type``
     - Optional
     - ``qualitative`` | ``quantitative``
     - Defines whether the question expects a discrete value or a numeric range.
       Defaults to ``qualitative``.
     - ``quantitative``
   * - ``test_lines/notes``
     - Optional
     - Text
     - Additional instructions displayed on the inspection line.
     - ``Target range 120-130 C``
   * - ``test_lines/uom_id/id``
     - Conditional
     - Module XML-ID
     - Unit of measure for quantitative questions. Leave empty for qualitative ones.
       If the unit has no external ID, use the next column instead.
     - ``uom.product_uom_celsius``
   * - ``test_lines/uom_id/name``
     - Conditional
     - Text
     - Human-readable unit name used when the XML-ID is missing (for example,
       ``Degrees Celsius``).
     - ``Degrees Celsius``
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
   * - ``test_lines/ql_values/name``
     - Conditional
     - Text
     - Qualitative option created under the question. Create extra rows for
       additional values.
     - ``Clear``
   * - ``test_lines/ql_values/ok``
     - Conditional
     - ``TRUE`` | ``FALSE``
     - Marks the qualitative option as acceptable. At least one value must be
       TRUE when qualitative options are defined.
     - ``TRUE``

Quick Start: Question-Only Import
---------------------------------

If you only need to prepare question banks for a quality test, you can keep the
template lean:

1. Fill in ``name`` with the test title and ``test_lines/name`` for every
   question you want to create.
2. Add one row per qualitative answer in ``test_lines/ql_values/name`` and mark
   the acceptable option by setting ``test_lines/ql_values/ok`` to ``TRUE``. At
   least one option per question must be marked as OK.
3. Leave all trigger and product columns empty to create generic tests that you
   can later assign manually on the product.
4. Skip ``type`` and ``test_lines/type`` unless you need quantitative questions.
   The loader defaults them to ``generic`` and ``qualitative``.
5. Omit ``test_lines/sequence`` to let the loader auto-assign ordering in steps
   of ten following the spreadsheet row order.

Example Dataset
---------------

The example below mirrors a minimal question-only file. You can copy/paste it
into the template or build your own spreadsheet following the same structure.

.. list-table:: Sample rows
   :header-rows: 1
   :widths: 28 28 24 10 10

   * - Test name (``name``)
     - Question (``test_lines/name``)
     - Option (``test_lines/ql_values/name``)
     - OK? (``test_lines/ql_values/ok``)
     - Notes (``test_lines/notes``)
   * - ``Incoming Visual Check``
     - ``Packaging Intact``
     - ``OK``
     - ``TRUE``
     - ``Verify packaging is sealed``
   * - ``Incoming Visual Check``
     - ``Packaging Intact``
     - ``Damaged``
     - ``FALSE``
     - ``Verify packaging is sealed``
   * - ``Incoming Visual Check``
     - ``Label Legible``
     - ``Readable``
     - ``TRUE``
     - ``-``

Filling Checklist
-----------------

#. Download the template and make a copy for your project.
#. Populate the rows with your test names, questions, and optional identifiers.
   Reuse the same ``code`` and ``test_lines/code`` values when you want to update
   existing records.
#. For qualitative questions, create one row per answer value and mark the
   acceptable option with ``TRUE``.
#. Leave product columns empty for tests that should stay generic and manually
   assign them later.
#. Save the file as ``.xlsx`` without changing the header names before running
   the import wizard.

.. include:: template_changelog.rst
