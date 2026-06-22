from odoo import api, fields, models


class MrpProduction(models.Model):
    _inherit = 'mrp.production'

    transfer_picking_ids = fields.Many2many(
        'stock.picking',
        string='Transfers'
    )
    transfer_count = fields.Integer(
        compute='_compute_transfer_count'
    )
    @api.depends('transfer_picking_ids')
    def _compute_transfer_count(self):
        for record in self:
            record.transfer_count = len(record.transfer_picking_ids)

    def action_open_transfer_wizard(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Create Transfer',
            'res_model': 'ecocarton.transfer.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_production_id': self.id,
            }
        }

    def action_view_transfers(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Transfers',
            'res_model': 'stock.picking',
            'view_mode': 'list,form',
            'domain': [('id', 'in', self.transfer_picking_ids.ids)],
        }