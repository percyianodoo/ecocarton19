import re
import string
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from odoo.osv import expression
from odoo.fields import Command


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    product = fields.Char(string='Product Code')

    @api.onchange('product_id')
    def onchange_product_id(self):
        product_id = self.env['product.product'].sudo().search([('id', '=', self.product_id.id)])
        if product_id:
            for product in product_id.product_customer_code_ids:
                if product.name_id.id == self.order_id.partner_id.id:
                    self.product = product.product_code

    def _prepare_invoice_line(self, **optional_values):
        res = super(SaleOrderLine, self)._prepare_invoice_line(**optional_values)
        res.update({'product_code_ids':self.product})
        return res


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    product_code_ids = fields.Char(string='Product Code')



