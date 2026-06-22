import re
import string
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from odoo.osv import expression


class ProductProductCode(models.Model):
    _name = "product.product.code"
    _description = " Product Code"

    code = fields.Char("Code")


class ProductProduct(models.Model):
    _inherit = "product.product"

    @api.model
    def _name_search(self, name, domain=None, operator='ilike', limit=None, order=None):
        res = super()._name_search(name, domain=domain, operator=operator, limit=limit, order=order)

        if self._context.get('partner_id'):
            partner_id = self._context.get('partner_id')
            supplier_ids = self.env['product.customer.code'].search([
            ('name_id', '=', partner_id),
            '|',
            ('product_code', operator, name),
            ('product_name', operator, name)
            ]).mapped('product_id')

        if supplier_ids:
            additional_domain = [('id', 'in', supplier_ids.ids)]
            res = self.search(expression.AND([domain or [], additional_domain]), limit=limit).ids

        return res
        

    @api.model
    def _search_display_name(self, operator, value):
        is_positive = operator not in expression.NEGATIVE_TERM_OPERATORS
        combine = expression.OR if is_positive else expression.AND

        domains = [
        [('name', operator, value)],
        [('default_code', operator, value)],
        ]

        if operator in ('=', 'in') or (operator.endswith('like') and is_positive):
            barcode_values = [value] if operator != 'in' else value
            domains.append([('barcode', 'in', barcode_values)])

        if operator == '=' and isinstance(value, str) and (m := re.search(r'\[(.*?)\]', value)):
            domains.append([('default_code', '=', m.group(1))])

        partner_id = self.env.context.get('partner_id')
        if partner_id:
            supplier_domain = [
            ('name_id', '=', partner_id),
            '|',
            ('product_code', operator, value),
            ('product_name', operator, value),
            ]
            supplier_product_ids = self.env['product.customer.code'].search(supplier_domain).mapped('product_id').ids

            if supplier_product_ids:
                domains.append([('id', 'in', supplier_product_ids)])

        return combine(domains)

    