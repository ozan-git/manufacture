# Copyright 2015 Oihane Crucelaegui - AvanzOSC
# Copyright 2018 Simone Rubino - Agile Business Group
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo.tests import Form, new_test_user
from odoo.tools import mute_logger

from odoo.addons.quality_control_oca.tests.test_quality_control import (
    TestQualityControlOcaBase,
)


class TestQualityControlStockOca(TestQualityControlOcaBase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.qc_trigger_model = cls.env["qc.trigger"]
        cls.picking_type_model = cls.env["stock.picking.type"]
        cls.partner1 = cls.env["res.partner"].create({"name": "Test partner 1"})
        cls.partner2 = cls.env["res.partner"].create({"name": "Test partner 2"})
        cls.picking_type = cls.env.ref("stock.picking_type_out")
        cls.location = cls.picking_type.default_location_src_id
        cls.location_dest = cls.picking_type.default_location_dest_id
        cls.trigger = cls.qc_trigger_model.search(
            [("picking_type_id", "=", cls.picking_type.id)]
        )
        cls.lot = cls.env["stock.lot"].create(
            {
                "name": "Lot for tests",
                "product_id": cls.product.id,
            }
        )
        cls.product.type = "consu"
        cls.product.is_storable = True
        cls.env["stock.quant"].create(
            {
                "product_id": cls.product.id,
                "location_id": cls.location.id,
                "quantity": 1,
                "lot_id": cls.lot.id,
            }
        )
        cls.user = new_test_user(
            cls.env,
            login="test_quality_control_stock_oca",
            groups=f"{'stock.group_stock_user'},{'quality_control_oca.group_quality_control_user'}",
        )
        picking_form = Form(
            cls.env["stock.picking"]
            .with_user(cls.user)
            .with_context(default_picking_type_id=cls.picking_type.id)
        )
        picking_form.partner_id = cls.partner1
        with picking_form.move_ids_without_package.new() as move_form:
            move_form.product_id = cls.product
            move_form.product_uom_qty = 2
        cls.picking1 = picking_form.save()
        cls.picking1.action_confirm()
        cls.picking1.move_ids.move_line_ids.quantity = 1

    @mute_logger("odoo.models.unlink")
    def test_inspection_create_for_product(self):
        self.product.qc_triggers = [
            (0, 0, {"trigger": self.trigger.id, "test": self.test.id})
        ]
        self.picking1._action_done()
        self.assertEqual(
            self.picking1.created_inspections, 1, "Only one inspection must be created"
        )
        inspection = self.picking1.qc_inspections_ids[:1]
        self.assertEqual(inspection.qty, self.picking1.move_ids.product_uom_qty)
        self.assertEqual(
            inspection.test, self.test, "Wrong test picked when creating inspection."
        )
        # Try in this context if onchange with an stock.pack.operation works
        inspection.qty = 5
        inspection.onchange_object_id()
        self.assertEqual(inspection.qty, self.picking1.move_ids.product_uom_qty)

    @mute_logger("odoo.models.unlink")
    def test_inspection_create_for_template(self):
        self.product.product_tmpl_id.qc_triggers = [
            (0, 0, {"trigger": self.trigger.id, "test": self.test.id})
        ]
        self.picking1._action_done()
        self.assertEqual(
            self.picking1.created_inspections, 1, "Only one inspection must be created"
        )
        self.assertEqual(
            self.picking1.qc_inspections_ids[:1].test,
            self.test,
            "Wrong test picked when creating inspection.",
        )

    @mute_logger("odoo.models.unlink")
    def test_inspection_create_for_category(self):
        self.product.categ_id.qc_triggers = [
            (0, 0, {"trigger": self.trigger.id, "test": self.test.id})
        ]
        self.picking1._action_done()
        self.assertEqual(
            self.picking1.created_inspections, 1, "Only one inspection must be created"
        )
        self.assertEqual(
            self.picking1.qc_inspections_ids[:1].test,
            self.test,
            "Wrong test picked when creating inspection.",
        )

    @mute_logger("odoo.models.unlink")
    def test_inspection_create_for_product_partner(self):
        self.product.qc_triggers = [
            (
                0,
                0,
                {
                    "trigger": self.trigger.id,
                    "test": self.test.id,
                    "partners": [(6, 0, self.partner1.ids)],
                },
            )
        ]
        self.picking1._action_done()
        self.assertEqual(
            self.picking1.created_inspections, 1, "Only one inspection must be created"
        )
        self.assertEqual(
            self.picking1.qc_inspections_ids[:1].test,
            self.test,
            "Wrong test picked when creating inspection.",
        )

    @mute_logger("odoo.models.unlink")
    def test_inspection_create_for_template_partner(self):
        self.product.product_tmpl_id.qc_triggers = [
            (
                0,
                0,
                {
                    "trigger": self.trigger.id,
                    "test": self.test.id,
                    "partners": [(6, 0, self.partner1.ids)],
                },
            )
        ]
        self.picking1._action_done()
        self.assertEqual(
            self.picking1.created_inspections, 1, "Only one inspection must be created"
        )
        self.assertEqual(
            self.picking1.qc_inspections_ids[:1].test,
            self.test,
            "Wrong test picked when creating inspection.",
        )

    @mute_logger("odoo.models.unlink")
    def test_inspection_create_for_category_partner(self):
        self.product.categ_id.qc_triggers = [
            (
                0,
                0,
                {
                    "trigger": self.trigger.id,
                    "test": self.test.id,
                    "partners": [(6, 0, self.partner1.ids)],
                },
            )
        ]
        self.picking1._action_done()
        self.assertEqual(
            self.picking1.created_inspections, 1, "Only one inspection must be created"
        )
        self.assertEqual(
            self.picking1.qc_inspections_ids[:1].test,
            self.test,
            "Wrong test picked when creating inspection.",
        )

    @mute_logger("odoo.models.unlink")
    def test_inspection_create_for_product_wrong_partner(self):
        self.product.qc_triggers = [
            (
                0,
                0,
                {
                    "trigger": self.trigger.id,
                    "test": self.test.id,
                    "partners": [(6, 0, self.partner2.ids)],
                },
            )
        ]
        self.picking1._action_done()
        self.assertEqual(
            self.picking1.created_inspections, 0, "No inspection must be created"
        )

    @mute_logger("odoo.models.unlink")
    def test_inspection_create_for_template_wrong_partner(self):
        self.product.product_tmpl_id.qc_triggers = [
            (
                0,
                0,
                {
                    "trigger": self.trigger.id,
                    "test": self.test.id,
                    "partners": [(6, 0, self.partner2.ids)],
                },
            )
        ]
        self.picking1._action_done()
        self.assertEqual(
            self.picking1.created_inspections, 0, "No inspection must be created"
        )

    @mute_logger("odoo.models.unlink")
    def test_inspection_create_for_category_wrong_partner(self):
        self.product.categ_id.qc_triggers = [
            (
                0,
                0,
                {
                    "trigger": self.trigger.id,
                    "test": self.test.id,
                    "partners": [(6, 0, self.partner2.ids)],
                },
            )
        ]
        self.picking1._action_done()
        self.assertEqual(
            self.picking1.created_inspections, 0, "No inspection must be created"
        )

    @mute_logger("odoo.models.unlink")
    def test_inspection_create_only_one(self):
        self.product.qc_triggers = [
            (0, 0, {"trigger": self.trigger.id, "test": self.test.id})
        ]
        self.product.categ_id.qc_triggers = [
            (0, 0, {"trigger": self.trigger.id, "test": self.test.id})
        ]
        self.picking1._action_done()
        self.assertEqual(
            self.picking1.created_inspections, 1, "Only one inspection must be created"
        )
        self.assertEqual(
            self.picking1.qc_inspections_ids[:1].test,
            self.test,
            "Wrong test picked when creating inspection.",
        )
        self.assertEqual(
            self.lot.created_inspections, 1, "Only one inspection must be created"
        )
        self.assertEqual(
            self.lot.qc_inspections_ids[:1].test,
            self.test,
            "Wrong test picked when creating inspection.",
        )

    def test_picking_type(self):
        picking_type = self.picking_type_model.create(
            {
                "name": "Test Picking Type",
                "code": "outgoing",
                "sequence_code": self.picking_type.sequence_code,
                "sequence_id": self.picking_type.sequence_id.id,
            }
        )
        trigger = self.qc_trigger_model.search(
            [("picking_type_id", "=", picking_type.id)]
        )
        self.assertEqual(len(trigger), 1, "One trigger must have been created.")
        self.assertEqual(
            trigger.name,
            picking_type.display_name,
            "Trigger name must match picking type display name.",
        )
        picking_type.write({"name": "Test Name Change"})
        self.assertEqual(
            trigger.name,
            picking_type.display_name,
            "Trigger name must match picking type display name.",
        )

    def test_qc_inspection_picking(self):
        self.inspection1.write(
            {
                "name": self.picking1.move_ids[:1]._name + "inspection",
                "object_id": "%s,%d" % (self.picking1._name, self.picking1.id),
            }
        )
        self.assertEqual(self.inspection1.picking_id, self.picking1)

    def test_qc_inspection_stock_move(self):
        self.inspection1.write(
            {
                "name": self.picking1.move_ids[:1]._name + "inspection",
                "object_id": "%s,%d"
                % (self.picking1.move_ids[:1]._name, self.picking1.move_ids[:1].id),
            }
        )
        self.inspection1.onchange_object_id()
        self.assertEqual(self.inspection1.picking_id, self.picking1)
        self.assertEqual(self.inspection1.lot_id, self.lot)
        self.assertEqual(
            self.inspection1.product_id, self.picking1.move_ids[:1].product_id
        )
        self.assertEqual(
            self.inspection1.qty, self.picking1.move_ids[:1].product_uom_qty
        )

    def test_qc_inspection_lot(self):
        self.inspection1.write(
            {
                "name": self.picking1.move_ids[:1]._name + "inspection",
                "object_id": "%s,%d" % (self.lot._name, self.lot.id),
            }
        )
        self.inspection1.onchange_object_id()
        self.assertEqual(self.inspection1.lot_id, self.lot)
        self.assertEqual(self.inspection1.product_id, self.lot.product_id)

    def _create_serial_picking(self, serials, per_lot=False, before=False):
        self.trigger.per_lot = per_lot
        if before:
            self.trigger.timing = "before"
        else:
            self.trigger.timing = "after"
        self.product.tracking = "serial"
        lots = [
            self.env["stock.lot"].create({"name": sn, "product_id": self.product.id})
            for sn in serials
        ]
        for lot in lots:
            self.env["stock.quant"].create(
                {
                    "product_id": self.product.id,
                    "location_id": self.location.id,
                    "quantity": 1,
                    "lot_id": lot.id,
                }
            )
        picking_form = Form(
            self.env["stock.picking"]
            .with_user(self.user)
            .with_context(default_picking_type_id=self.picking_type.id)
        )
        picking_form.partner_id = self.partner1
        with picking_form.move_ids_without_package.new() as move_form:
            move_form.product_id = self.product
            move_form.product_uom_qty = len(serials)
        picking = picking_form.save()
        picking.action_confirm()
        move = picking.move_ids[0]
        move.move_line_ids.unlink()
        for lot in lots:
            self.env["stock.move.line"].create(
                {
                    "move_id": move.id,
                    "product_id": self.product.id,
                    "qty_done": 1,
                    "location_id": self.location.id,
                    "location_dest_id": self.location_dest.id,
                    "lot_id": lot.id,
                }
            )
        self.product.qc_triggers = [
            (0, 0, {"trigger": self.trigger.id, "test": self.test.id})
        ]
        picking._action_done()
        return picking

    def test_serial_single_inspection(self):
        picking = self._create_serial_picking(["sn1", "sn2", "sn3"], per_lot=False)
        self.assertEqual(picking.created_inspections, 1)

    def test_serial_after_per_lot(self):
        picking = self._create_serial_picking(["sn1", "sn2", "sn3"], per_lot=True)
        self.assertEqual(picking.created_inspections, 3)

    def test_serial_before_per_lot(self):
        picking = self._create_serial_picking(
            ["sn1", "sn2", "sn3"], per_lot=True, before=True
        )
        self.assertEqual(picking.created_inspections, 3)

    def test_lot_per_lot(self):
        self.trigger.per_lot = True
        self.product.tracking = "lot"
        lots = [
            self.env["stock.lot"].create(
                {"name": f"lot{i}", "product_id": self.product.id}
            )
            for i in range(1, 3)
        ]
        for lot in lots:
            self.env["stock.quant"].create(
                {
                    "product_id": self.product.id,
                    "location_id": self.location.id,
                    "quantity": 1,
                    "lot_id": lot.id,
                }
            )
        picking_form = Form(
            self.env["stock.picking"]
            .with_user(self.user)
            .with_context(default_picking_type_id=self.picking_type.id)
        )
        picking_form.partner_id = self.partner1
        with picking_form.move_ids_without_package.new() as move_form:
            move_form.product_id = self.product
            move_form.product_uom_qty = 2
        picking = picking_form.save()
        picking.action_confirm()
        move = picking.move_ids[0]
        move.move_line_ids.unlink()
        for lot in lots:
            self.env["stock.move.line"].create(
                {
                    "move_id": move.id,
                    "product_id": self.product.id,
                    "qty_done": 1,
                    "location_id": self.location.id,
                    "location_dest_id": self.location_dest.id,
                    "lot_id": lot.id,
                }
            )
        self.product.qc_triggers = [
            (0, 0, {"trigger": self.trigger.id, "test": self.test.id})
        ]
        picking._action_done()
        self.assertEqual(picking.created_inspections, 2)

    def test_lot_per_lot_multiple_moves(self):
        self.trigger.per_lot = True
        self.product.tracking = "lot"
        lots = [
            self.env["stock.lot"].create(
                {"name": f"lot-move-{i}", "product_id": self.product.id}
            )
            for i in range(1, 3)
        ]
        for lot in lots:
            self.env["stock.quant"].create(
                {
                    "product_id": self.product.id,
                    "location_id": self.location.id,
                    "quantity": 1,
                    "lot_id": lot.id,
                }
            )
        picking_form = Form(
            self.env["stock.picking"]
            .with_user(self.user)
            .with_context(default_picking_type_id=self.picking_type.id)
        )
        picking_form.partner_id = self.partner1
        for _ in lots:
            with picking_form.move_ids_without_package.new() as move_form:
                move_form.product_id = self.product
                move_form.product_uom_qty = 1
        picking = picking_form.save()
        picking.action_confirm()
        for move, lot in zip(picking.move_ids, lots):
            move.move_line_ids.unlink()
            self.env["stock.move.line"].create(
                {
                    "move_id": move.id,
                    "product_id": self.product.id,
                    "qty_done": 1,
                    "location_id": self.location.id,
                    "location_dest_id": self.location_dest.id,
                    "lot_id": lot.id,
                }
            )
        self.product.qc_triggers = [
            (0, 0, {"trigger": self.trigger.id, "test": self.test.id})
        ]
        picking._action_done()
        self.assertEqual(picking.created_inspections, 2)

    def test_no_tracking_per_lot(self):
        self.trigger.per_lot = True
        self.product.tracking = "none"
        picking_form = Form(
            self.env["stock.picking"]
            .with_user(self.user)
            .with_context(default_picking_type_id=self.picking_type.id)
        )
        picking_form.partner_id = self.partner1
        with picking_form.move_ids_without_package.new() as move_form:
            move_form.product_id = self.product
            move_form.product_uom_qty = 3
        picking = picking_form.save()
        picking.action_confirm()
        self.product.qc_triggers = [
            (0, 0, {"trigger": self.trigger.id, "test": self.test.id})
        ]
        picking._action_done()
        self.assertEqual(picking.created_inspections, 1)

    def test_duplicate_inspection_prevention(self):
        picking = self._create_serial_picking(["sn1"], per_lot=True)
        initial = picking.created_inspections
        picking._action_done()
        self.assertEqual(picking.created_inspections, initial)

    def test_multiple_products_generate_multiple_inspections(self):
        """Each product on a picking should create its own inspection."""
        product_b = self.product.copy({"name": "Test product B"})
        self.env["stock.quant"].create(
            {
                "product_id": product_b.id,
                "location_id": self.location.id,
                "quantity": 1,
            }
        )
        product_b.qc_triggers = [
            (0, 0, {"trigger": self.trigger.id, "test": self.test.id})
        ]
        self.product.qc_triggers = [
            (0, 0, {"trigger": self.trigger.id, "test": self.test.id})
        ]

        picking_form = Form(
            self.env["stock.picking"]
            .with_user(self.user)
            .with_context(default_picking_type_id=self.picking_type.id)
        )
        picking_form.partner_id = self.partner1
        with picking_form.move_ids_without_package.new() as move_form:
            move_form.product_id = self.product
            move_form.product_uom_qty = 1
        with picking_form.move_ids_without_package.new() as move_form:
            move_form.product_id = product_b
            move_form.product_uom_qty = 1
        picking = picking_form.save()
        picking.action_confirm()
        picking._action_done()

        self.assertEqual(picking.created_inspections, 2)
