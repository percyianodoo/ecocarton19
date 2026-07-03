from odoo import models, _, api, fields


class StockMove(models.Model):
    _inherit = 'stock.move'


    def _prepare_procurement_origin(self):
        self.ensure_one()
        if self.env.context.get('from_generate_mo_button'):
            return self.origin or self.picking_id.display_name or (self.reference_ids and self.reference_ids[0].name)
        return super()._prepare_procurement_origin()