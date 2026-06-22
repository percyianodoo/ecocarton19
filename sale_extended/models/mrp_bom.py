from odoo import api, fields, models
from odoo.exceptions import ValidationError


# from odoo.tools.safe_eval import safe_eval, test_python_expr

class MRPBom(models.Model):
    _inherit = "mrp.bom"

    pcs_cut_per_sheet = fields.Float(string="Pcs cut per sheet",copy=False)
    length = fields.Float(string="Length",copy=False)