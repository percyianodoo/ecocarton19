from odoo import fields, models


class MrpBomLine(models.Model):
    _inherit = "mrp.bom.line"

    custom_product_category_id = fields.Many2one(
        "product.category",
        string="Product Category",
    )