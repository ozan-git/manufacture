# Copyright 2014 Serv. Tec. Avanzados - Pedro M. Baeza
# Copyright 2018 Simone Rubino - Agile Business Group
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models
from odoo.fields import first


def _done_qty(ml):
    return getattr(ml, "qty_done", getattr(ml, "quantity", 0.0))


def _planned_qty(ml):
    return getattr(ml, "product_uom_qty", 0.0)


class QcInspection(models.Model):
    _inherit = "qc.inspection"

    picking_id = fields.Many2one(
        comodel_name="stock.picking", compute="_compute_picking", store=True
    )
    lot_id = fields.Many2one(
        comodel_name="stock.lot", compute="_compute_lot", store=True
    )

    def object_selection_values(self):
        result = super().object_selection_values()
        result.extend(
            [
                ("stock.picking", "Picking List"),
                ("stock.move", "Stock Move"),
                ("stock.lot", "Lot/Serial Number"),
            ]
        )
        return result

    @api.depends("object_id")
    def _compute_picking(self):
        for inspection in self.filtered("object_id"):
            if inspection.object_id._name == "stock.move":
                inspection.picking_id = inspection.object_id.picking_id
            elif inspection.object_id._name == "stock.picking":
                inspection.picking_id = inspection.object_id

    @api.depends("object_id")
    def _compute_lot(self):
        moves = self.filtered(
            lambda i: i.object_id and i.object_id._name == "stock.move"
        ).mapped("object_id")
        move_lines = self.env["stock.move.line"].search(
            [("lot_id", "!=", False), ("move_id", "in", [move.id for move in moves])]
        )
        for inspection in self.filtered("object_id"):
            if inspection.object_id._name == "stock.move":
                inspection.lot_id = first(
                    move_lines.filtered(
                        lambda x, inspection=inspection: x.move_id
                        == inspection.object_id
                    )
                ).lot_id
            elif inspection.object_id._name == "stock.lot":
                inspection.lot_id = inspection.object_id

    @api.depends("object_id")
    def _compute_product_id(self):
        """Overriden for getting the product from a stock move."""
        res = super()._compute_product_id()
        for inspection in self.filtered("object_id"):
            if inspection.object_id._name == "stock.move":
                inspection.product_id = inspection.object_id.product_id
            elif inspection.object_id._name == "stock.lot":
                inspection.product_id = inspection.object_id.product_id
        return res

    @api.onchange("object_id")
    def onchange_object_id(self):
        if self.object_id and self.object_id._name == "stock.move":
            self.qty = self.object_id.product_qty

    def _prepare_inspection_header(self, object_ref, trigger_line):
        res = super()._prepare_inspection_header(object_ref, trigger_line)
        # Fill qty when coming from pack operations
        if object_ref and object_ref._name == "stock.move":
            res["qty"] = object_ref.product_uom_qty
        return res

    def _inspection_exists_per_lot(self, picking, product, lot, trigger_line):
        test_rec = getattr(
            trigger_line, "test_id", getattr(trigger_line, "test", False)
        )

        domain = [
            ("picking_id", "=", picking.id),
            ("product_id", "=", product.id),
            ("lot_id", "=", lot.id),
        ]
        if test_rec:
            domain.append(("test", "=", getattr(test_rec, "id", test_rec)))

        return bool(self.search_count(domain))

    def _make_inspection(self, object_ref, trigger_line):
        trigger = trigger_line.trigger
        product = object_ref.product_id if object_ref._name == "stock.move" else False
        per_lot = trigger.per_lot
        if (
            object_ref._name == "stock.move"
            and product
            and product.tracking == "serial"
        ):
            per_lot = True
        if (
            per_lot
            and object_ref._name == "stock.move"
            and object_ref.product_id.tracking in ("serial", "lot")
        ):
            picking = object_ref.picking_id
            groups = {}
            for ml in picking.move_line_ids:
                if ml.product_id != product:
                    continue
                done_qty = _done_qty(ml)
                planned_qty = _planned_qty(ml)
                if not ml.lot_id or not (done_qty or planned_qty):
                    continue
                lot = ml.lot_id
                qty = done_qty or planned_qty
                if product.tracking == "serial":
                    qty = 1.0
                groups.setdefault(lot.id, {"lot": lot, "qty": 0})
                groups[lot.id]["qty"] += qty
            inspections = self.browse()
            for data in groups.values():
                if self._inspection_exists_per_lot(
                    picking,
                    product,
                    data["lot"],
                    trigger_line,
                ):
                    continue
                inspection = super()._make_inspection(picking, trigger_line)
                test_rec = getattr(
                    trigger_line, "test_id", getattr(trigger_line, "test", False)
                )
                vals = {
                    "product_id": product.id,
                    "qty": data["qty"],
                    "lot_id": data["lot"].id,
                }
                if test_rec:
                    vals["test"] = getattr(test_rec, "id", test_rec)
                inspection.write(vals)
                inspections |= inspection
            return inspections
        return super()._make_inspection(object_ref, trigger_line)


class QcInspectionLine(models.Model):
    _inherit = "qc.inspection.line"

    picking_id = fields.Many2one(
        comodel_name="stock.picking", related="inspection_id.picking_id", store=True
    )
    lot_id = fields.Many2one(
        comodel_name="stock.lot", related="inspection_id.lot_id", store=True
    )
