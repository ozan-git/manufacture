# Copyright 2010 NaN Projectes de Programari Lliure, S.L.
# Copyright 2014 Serv. Tec. Avanzados - Pedro M. Baeza
# Copyright 2014 Oihane Crucelaegui - AvanzOSC
# Copyright 2017 ForgeFlow S.L.
# Copyright 2017 Simone Rubino - Agile Business Group
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


def _filter_trigger_lines(trigger_lines, product=None, record=None):
    filtered_trigger_lines = []
    unique_keys = set()
    record_key = False
    if record:
        record_key = getattr(record, "id", False)
        origin = getattr(record, "_origin", False)
        if not record_key and origin:
            record_key = getattr(origin, "id", False)
        if not record_key:
            record_key = id(record)
    for trigger_line in trigger_lines:
        test = trigger_line.test
        test_id = test.id if test else False
        product_id = product.id if product else False
        key = (test_id, product_id, record_key)
        if key not in unique_keys:
            filtered_trigger_lines.append(trigger_line)
            unique_keys.add(key)
    return filtered_trigger_lines


class QcTriggerLine(models.AbstractModel):
    _name = "qc.trigger.line"
    _inherit = "mail.thread"
    _description = "Abstract line for defining triggers"

    trigger = fields.Many2one(comodel_name="qc.trigger", required=True)
    test = fields.Many2one(comodel_name="qc.test", required=True)
    user = fields.Many2one(
        comodel_name="res.users",
        string="Responsible",
        tracking=True,
        default=lambda self: self.env.user,
    )
    partners = fields.Many2many(
        comodel_name="res.partner",
        help="If filled, the test will only be created when the action is done"
        " for one of the specified partners. If empty, the test will always be"
        " created.",
        domain="[('parent_id', '=', False)]",
    )
    timing = fields.Selection(
        selection=[
            ("before", "Before"),
            ("after", "After"),
            ("plan_ahead", "Plan Ahead"),
        ],
        default="after",
        help="* Before: An executable inspection is generated before the record "
        "related to the trigger is completed (e.g. when picking is confirmed).\n"
        "* After: An executable inspection is generated when the record related to the "
        "trigger is completed (e.g. when picking is done).\n"
        "* Plan Ahead: A non-executable inspection is generated before the record "
        "related to the trigger is completed (e.g. when picking is confirmed), and the "
        "inspection becomes executable when the record related to the trigger is "
        "completed (e.g. when picking is done).",
    )

    def get_trigger_line_for_product(self, trigger, timings, product, partner=False):
        """Overridable method for getting trigger_line associated to a product.
        Each inherited model will complete this module to make the search by
        product, template or category.
        :param trigger: Trigger instance.
        :param product: Product instance.
        :return: Set of trigger_lines that matches to the given product and
        trigger.
        """
        return set()
