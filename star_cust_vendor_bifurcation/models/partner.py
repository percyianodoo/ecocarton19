# -*- coding: utf-8 -*-
# Part of The Stella Technolabs. See LICENSE file for full copyright and licensing details.

from odoo import fields, models


class ResPartner(models.Model):
    _inherit = 'res.partner'

    is_customer = fields.Boolean(string="Customer")
    is_vendor = fields.Boolean(string="Vendor")
