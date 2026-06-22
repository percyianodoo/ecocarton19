import string
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    product_customer_code = fields.Boolean(string="Product Customer Code", related="company_id.product_customer_code",
                                           readonly=False)


class InheritResCompany(models.Model):
    _inherit = 'res.company'

    product_customer_code = fields.Boolean(string="Code")
