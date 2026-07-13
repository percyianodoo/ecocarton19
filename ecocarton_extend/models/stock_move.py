from odoo import fields, models

class StockMove(models.Model):
    _inherit = "stock.move"

    custom_product_category_id = fields.Many2one(
        "product.category",
        string="Product Category",
    )