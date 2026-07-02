from odoo import _, fields, models, api
from odoo.exceptions import UserError


class EcocartonTransferWizard(models.TransientModel):
    _name = 'ecocarton.transfer.wizard'
    _description = 'Ecocarton Transfer Wizard'

    production_id = fields.Many2one(
        'mrp.production',
        required=True
    )
    transfer_type = fields.Selection([
        ('picking_list', 'Picking List'),
        ('packing', 'Packing'),
    ], required=True)
    source_location_id = fields.Many2one(
        'stock.location',
        string='Source Location'
    )
    destination_location_id = fields.Many2one(
        'stock.location',
        string='Destination Location'
    )
    packing_qty = fields.Float(
        string='Packing Quantity',
        default=0.0
    )

    @api.onchange('transfer_type')
    def _onchange_transfer_type(self):
        self.packing_qty = 0.0
        if self.transfer_type == 'picking_list':
            stock_location = self.env['stock.location'].search([
                ('complete_name', '=', 'WH/Stock')
            ], limit=1)
            self.source_location_id = stock_location
        else:
            self.source_location_id = False

    def action_create_transfer(self):
        self.ensure_one()

        if self.transfer_type == 'picking_list':
            return self._create_picking_list_transfer()

        return self._create_packing_transfer()

    def _create_picking_list_transfer(self):
        production = self.production_id

        if not self.destination_location_id:
            raise UserError(_("Please select Destination Location."))

        picking_type = self.env['stock.picking.type'].search([
            ('code', '=', 'internal'),
            ('sequence_code', '=', 'PC'),
            ('company_id', '=', self.env.company.id),
        ], limit=1)

        if not picking_type:
            raise UserError(
                _("Pick Components operation type not found.")
            )
        move_lines = []
        for move in production.move_raw_ids.filtered(
                lambda m: m.product_uom_qty > 0):

            move_lines.append((0, 0, {
                # 'name': move.product_id.display_name,
                'product_id': move.product_id.id,
                'product_uom_qty': move.product_uom_qty,
                'product_uom': move.product_uom.id,
                'location_id': self.source_location_id.id,
                'location_dest_id': self.destination_location_id.id,
            }))
        if not move_lines:
            raise UserError(_("No component lines found."))

        picking = self.env['stock.picking'].create({
            'picking_type_id': picking_type.id,
            'location_id': self.source_location_id.id,
            'location_dest_id': self.destination_location_id.id,
            'origin': production.name,
            'move_ids': move_lines,
        })
        picking.action_confirm()
        picking.message_post(
            body=_(
                "This transfer was created from the custom Create Transfer button on Manufacturing Order %s.") % production.name
        )
        production.transfer_picking_ids = [(4, picking.id)]

        return {
            'type': 'ir.actions.act_window',
            'res_model': 'stock.picking',
            'res_id': picking.id,
            'view_mode': 'form',
            'target': 'current',
        }

    def _create_packing_transfer(self):
        self.ensure_one()
        production = self.production_id
        if not self.source_location_id:
            raise UserError(_("Please select Source Location."))
        if not self.destination_location_id:
            raise UserError(_("Please select Destination Location."))
        if self.packing_qty <= 0:
            raise UserError(_("Please enter Packing Quantity."))
        packing_type = self.env['stock.picking.type'].search([
            ('code', '=', 'internal'),
            ('sequence_code', '=', 'SFP'),
            ('company_id', '=', self.env.company.id),
        ], limit=1)
        if not packing_type:
            raise UserError(
                _("Pack operation type not found.")
            )
        picking = self.env['stock.picking'].create({
            'picking_type_id': packing_type.id,
            'location_id': self.source_location_id.id,
            'location_dest_id': self.destination_location_id.id,
            'origin': production.name,
            'move_ids': [(0, 0, {
                # 'name': production.product_id.display_name,
                'product_id': production.product_id.id,
                'product_uom_qty': self.packing_qty,
                'product_uom': production.product_uom_id.id,
                'location_id': self.source_location_id.id,
                'location_dest_id': self.destination_location_id.id,
            })],
        })
        picking.action_confirm()
        picking.message_post(
            body=_(
                "This transfer was created from the custom Create Transfer button on Manufacturing Order %s.") % production.name
        )
        production.transfer_picking_ids = [(4, picking.id)]
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'stock.picking',
            'res_id': picking.id,
            'view_mode': 'form',
            'target': 'current',
        }