import string
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from odoo.osv import expression


class ProductCustomerCode(models.Model):
    _name = "product.customer.code"
    _description = "Customers Code"
    _rec_name = 'product_code'

    product_code = fields.Char('Customer Product Code', required=True)
    name_id = fields.Many2one('res.partner', 'Customer', required=True, )
    product_id = fields.Many2one(
        'product.product', string="Product Name ", required=True, )
    name_ids = fields.Many2one('product.template', string="Name")
    product_tmpl_id = fields.Many2one(
        'product.template', 'Product Template', check_company=True,
        index=True, ondelete='cascade')
    product_name = fields.Char("Product Name")


class ProductTemplate(models.Model):
    _inherit = "product.template"

    @api.model
    def _compute_customer_code(self):
        res = self.env['res.config.settings'].sudo().search(
            [], limit=1, order="id desc")
        for record in self:
            record.product_customer_code = res.product_customer_code

    product_customer_code_ids = fields.One2many(
        'product.customer.code', 'product_tmpl_id', string='Product customer codes',
        copy=False)
    product_code = fields.Char('Customer Product Code',
                               related="product_customer_code_ids.product_code",
                               store=True)
    product_customer_code = fields.Boolean(string="Customer Code", compute='_compute_customer_code')

