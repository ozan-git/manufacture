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
   * - ``product_template_default_code``
     - Optional
     - Text
     - Internal reference of the product template used to bind the trigger.
       Leave empty to keep the test generic.
     - ``FERT-001``
   * - ``product_template_name``
     - Optional
     - Text
     - Human-readable product template name; used for review only.
     - ``Sterilized Filter``
   * - ``test_code``
     - Required
     - Text (unique per test)
     - Identifier used to create or update the related ``qc.test``.
     - ``STERIL_TEST``
   * - ``test_name``
     - Required
     - Text
     - Display name of the quality test.
     - ``Sterility Check``
   * - ``test_type``
     - Required
     - ``generic`` | ``related``
     - Determines whether the test is generic or linked to a specific model.
     - ``related``
   * - ``test_category_xmlid``
     - Optional
     - Module XML-ID
     - Reference to an existing ``qc.test.category`` record (``module.record``).
     - ``quality_control_oca.qc_test_category_process``
   * - ``fill_correct_values``
     - Optional
     - ``TRUE`` | ``FALSE``
     - Pre-fill inspection lines with the "OK" values when the inspection is created.
     - ``TRUE``
   * - ``trigger_name``
     - Optional
     - Text
     - Name of the ``qc.trigger`` to use when creating the
       ``qc.trigger.product_template_line``.
     - ``Manufacturing Order``
   * - ``trigger_timing``
     - Optional
     - ``before`` | ``after`` | ``plan_ahead``
     - Timing applied to the trigger line when the product template is filled.
     - ``after``
   * - ``question_sequence``
     - Required
     - Integer
     - Sequence used to order the questions within the test.
     - ``10``
   * - ``question_code``
     - Required
     - Text (unique per test)
     - Identifier to help detect and update existing questions.
     - ``STER_TEMP``
   * - ``question_name``
     - Required
     - Text
     - Label shown on the inspection line.
     - ``Sterilization Temperature``
   * - ``question_type``
     - Required
     - ``qualitative`` | ``quantitative``
     - Defines whether the question expects a discrete value or a numeric range.
     - ``quantitative``
   * - ``question_notes``
     - Optional
     - Text
     - Additional instructions displayed on the inspection line.
     - ``Target range 120-130 C``
   * - ``uom_xmlid``
     - Conditional
     - Module XML-ID
     - Unit of measure for quantitative questions. Leave empty for qualitative ones.
     - ``uom.product_uom_celsius``
   * - ``min_value``
     - Conditional
     - Number
     - Minimum accepted value for quantitative questions.
     - ``120``
   * - ``max_value``
     - Conditional
     - Number
     - Maximum accepted value for quantitative questions.
     - ``130``
   * - ``qualitative_value_name``
     - Conditional
     - Text
     - Qualitative option created under the question. Create extra rows for
       additional values.
     - ``Clear``
   * - ``qualitative_value_ok``
     - Conditional
     - ``TRUE`` | ``FALSE``
     - Marks the qualitative option as acceptable. At least one value must be
       TRUE when qualitative options are defined.
     - ``TRUE``

Example Dataset
---------------

The template ships with a sample set of rows to illustrate quantitative and
qualitative questions. You can keep them as a reference or delete them before
importing real data.

.. list-table:: Sample rows
   :header-rows: 1
   :widths: 16 14 12 18 10 18 10 16

   * - Test code
     - Question code
     - Question type
     - Qualitative value
     - OK?
     - UoM
     - Min
     - Max
   * - ``STERIL_TEST``
     - ``STER_TEMP``
     - ``quantitative``
     - ``-``
     - ``-``
     - ``uom.product_uom_celsius``
     - ``120``
     - ``130``
   * - ``STERIL_TEST``
     - ``STER_COLOR``
     - ``qualitative``
     - ``Clear``
     - ``TRUE``
     - ``-``
     - ``-``
     - ``-``
   * - ``STERIL_TEST``
     - ``STER_COLOR``
     - ``qualitative``
     - ``Amber``
     - ``FALSE``
     - ``-``
     - ``-``
     - ``-``

Filling Checklist
-----------------

#. Download the template and make a copy for your project.
#. Replace the sample rows with your product and test data. Reuse the same
   ``test_code`` and ``question_code`` when you want to update existing records.
#. For qualitative questions, create one row per answer value and mark the
   acceptable option with ``TRUE``.
#. Leave product columns empty for tests that should stay generic and manually
   assign them later.
#. Save the file as ``.xlsx`` without changing the header names before running
   the import wizard.

.. include:: template_changelog.rst
