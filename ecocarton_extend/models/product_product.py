import logging
_logger = logging.getLogger(__name__)
from odoo import fields, models, api


from odoo import api, models
from odoo.osv import expression



class ProductProduct(models.Model):
    _inherit = "product.product"

    @api.model
    @api.readonly
    def web_name_search(self, name, specification, domain=None, operator='ilike', limit=100):
        domain = domain or []

        category_id = self.env.context.get("component_category_id")
        if category_id:
            domain = expression.AND([
                domain,
                [('categ_id', '=', category_id)],
            ])

        return super().web_name_search(name,specification,domain=domain,operator=operator,limit=limit,)


    @api.model
    @api.readonly
    def web_search_read(self,domain,specification,offset=0,limit=None,order=None,count_limit=None,):
        category_id = self.env.context.get("component_category_id")
        if category_id:
            domain = expression.AND([
                domain or [],
                [('categ_id', '=', category_id)],
            ])
        return super().web_search_read(domain,specification,offset=offset,limit=limit,order=order,count_limit=count_limit,)

