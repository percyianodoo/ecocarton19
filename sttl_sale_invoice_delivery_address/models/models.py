# -*- coding: utf-8 -*-

from odoo import models, fields, api


class sale_invoice_delivery_address(models.Model):

    _inherit = 'sale.order'
    parent_id = fields.Many2one(related='partner_id.parent_id')

    partner_invoice_id = fields.Many2one(
        comodel_name='res.partner',
        string="Invoice Address",
        domain="[('type', '=', 'invoice'), '|', ('id', 'child_of', partner_id), ('id', 'child_of', parent_id)]")

    partner_shipping_id = fields.Many2one(
        comodel_name='res.partner',
        string="Delivery Address",
        domain="[('type', '=', 'delivery'), '|', ('id', 'child_of', partner_id), ('id', 'child_of', parent_id)]")
