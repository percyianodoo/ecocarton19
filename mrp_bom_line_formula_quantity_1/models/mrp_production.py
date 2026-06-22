#  Copyright 2024 Simone Rubino - Aion Tech
#  License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models, api


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
        grouped_stock_pickings = self.env['stock.picking']._read_group(
            domain=[('group_id', 'in', self.procurement_group_id.ids), ('group_id', '!=', False)],
            aggregates=['id:recordset'],
            groupby=['group_id'],
        )
        pickings_per_procurement_group = {
            group_id.id: picking_ids.sorted() for group_id, picking_ids in grouped_stock_pickings
        }
        for order in self:
            pickings = pickings_per_procurement_group.get(
                order.procurement_group_id.id,
                self.env['stock.picking']
            )
            # custom code to view related picking only before it shows all picking of backorders too.
            normal_pickings = pickings.filtered(
                lambda p: p.picking_type_id.sequence_code != 'SFP'
            )
            sfp_pickings = pickings.filtered(
                lambda p:
                p.picking_type_id.sequence_code == 'SFP'
                and p.origin == order.name
            )
            order.picking_ids = normal_pickings | sfp_pickings
            # custom code end

            order.picking_ids |= order.move_raw_ids.move_orig_ids.picking_id
            order.delivery_count = len(order.picking_ids)


class StockMove(models.Model):
    _inherit = 'stock.move'

    def _search_picking_for_assignation_domain(self):
        domain = super()._search_picking_for_assignation_domain()

        # custom code for to stop sfp picking from merging with one picking
        if self.picking_type_id.sequence_code == 'SFP':
            domain.append((
                'origin',
                '=',
                self.origin
            ))
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