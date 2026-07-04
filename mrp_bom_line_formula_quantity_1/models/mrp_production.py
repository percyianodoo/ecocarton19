#  Copyright 2024 Simone Rubino - Aion Tech
#  License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models, api
from odoo.fields import Domain


class MRPProduction(models.Model):
    _inherit = "mrp.production"

    def _get_move_raw_values(
            self,
            product,
            product_uom_qty,
            product_uom,
            operation_id=False,
            bom_line=False,
    ):
        values = super()._get_move_raw_values(
            product,
            product_uom_qty,
            product_uom,
            operation_id=operation_id,
            bom_line=bom_line,
        )
        if bom_line:
            computed_quantity = bom_line._eval_quantity_formula(
                product,
                product_uom,
                product_uom_qty,
                self,
                operation_id=operation_id,
            )
            if computed_quantity is not None:
                values["product_uom_qty"] = computed_quantity
        return values

    @api.depends('state')
    def _compute_picking_ids(self):
        move_per_production_group = self.env['stock.move']._read_group(
            [('production_group_id', 'in', self.production_group_id.ids)],
            ['production_group_id'],
            ['picking_id:recordset'],
        )

        move_per_production = {
            group: pickings
            for group, pickings in move_per_production_group
        }

        for order in self:
            pickings = move_per_production.get(
                order.production_group_id,
                self.env['stock.picking']
            )

            normal_pickings = pickings.filtered(
                lambda p: p.picking_type_id.sequence_code != 'SFP'
            )

            sfp_pickings = pickings.filtered(
                lambda p: p.picking_type_id.sequence_code == 'SFP'
                          and p.origin == order.name
            )

            order.picking_ids = (
                    normal_pickings
                    | sfp_pickings
                    | order.move_raw_ids.move_orig_ids.picking_id
            )

            order.delivery_count = len(order.picking_ids)


class StockMove(models.Model):
    _inherit = 'stock.move'

    def _search_picking_for_assignation_domain(self):
        domain = super()._search_picking_for_assignation_domain()

        # custom code for to stop sfp picking from merging with one picking
        if self.picking_type_id.sequence_code == 'SFP':
            domain = Domain.AND([
                domain,
                Domain('origin', '=', self.origin),
            ])

        return domain


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    @api.depends('reference_ids.production_ids')
    def _compute_production_ids(self):
        super()._compute_production_ids()

        for picking in self.filtered(
                lambda p: p.picking_type_id.sequence_code == 'SFP'
        ):
            picking.production_ids = picking.production_ids.filtered(
                lambda p: p.name == picking.origin
            )
