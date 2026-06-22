from odoo import models, _, api, fields
from odoo.tools import float_compare, float_round, float_is_zero, format_datetime
import re

class MrpProduction(models.Model):
    _inherit = 'mrp.production'

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get('name') or vals['name'] == _('New'):
                origin = vals.get('origin')
                if origin:
                    parent_mo = self.search([('name', '=', origin)], limit=1)

                    if parent_mo:
                        root_mo = parent_mo
                        while root_mo.origin and self.search([('name', '=', root_mo.origin)], limit=1):
                            root_mo = self.search([('name', '=', root_mo.origin)], limit=1)

                        sale_order = self.env['sale.order'].search([('name', '=', root_mo.origin)], limit=1)

                        if sale_order:
                            if not sale_order.sub_mo_counter:
                                sale_order.sub_mo_counter = 0

                            sale_order.sub_mo_counter += 1
                            vals['name'] = f"{root_mo.name}-{sale_order.sub_mo_counter}"
                    else:
                        picking_type_id = vals.get('picking_type_id')
                        if not picking_type_id:
                            picking_type_id = self._get_default_picking_type_id(
                                vals.get('company_id', self.env.company.id))
                            vals['picking_type_id'] = picking_type_id
                        vals['name'] = self.env['stock.picking.type'].browse(picking_type_id).sequence_id.next_by_id()
                        vals['bom_id'] = self.env.context.get('bom_id')
                        if self.env.context.get('selected_so_line_id'):
                            mo_calculations_id = self.env['mo.calculation'].search([('sale_line_id.id','=',self.env.context.get('selected_so_line_id'))],limit=1)
                            if mo_calculations_id:
                                vals['product_qty'] = mo_calculations_id.x_studio_wastage_calculation
        return super().create(vals_list)

    def _update_raw_moves(self, factor):
        self.ensure_one()
        update_info = []
        number_pattern = r"-?\d+(?:\.\d+)?"
        for move in self.move_raw_ids.filtered(lambda m: m.state not in ('done', 'cancel')):
            old_qty = move.product_uom_qty
            new_qty = float_round(old_qty * factor, precision_rounding=move.product_uom.rounding, rounding_method='UP')
            if move.bom_line_id.quantity_formula:
                res = re.findall(number_pattern, move.bom_line_id.quantity_formula)
                if len(res) >= 1:
                    new_qty = float(res[0])
                    # components.with_context(bypass_procurement_creation=True,
                    #                         no_procurement=True).product_uom_qty = new_qty
            if new_qty > 0:
                # procurement and assigning is now run in write
                move.write({'product_uom_qty': new_qty})
                update_info.append((move, old_qty, new_qty))
        return update_info
