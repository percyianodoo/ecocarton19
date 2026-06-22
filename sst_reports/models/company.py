from odoo import api, fields, models,_
from datetime import timedelta, date
from dateutil.relativedelta import relativedelta
from odoo.exceptions import ValidationError


class CompanySSt(models.Model):
    _inherit = 'res.company'


    sst_number=fields.Char('SST NUMBER')



class SSTTax(models.Model):
    _inherit = 'account.tax'

    # tax_label=fields.Selection([('s10','S-10'),('s5','S-5'),('su','SU'),('st5','ST5'),('su5','SU5'),('suv','SUV'),('sv','SV')],string='Label')
    # label_description=fields.Char()
    tax_code_id=fields.Many2one('account.tax.code')


    # @api.onchange('tax_label')
    # def change_label(self):
    #     if self.tax_label:
    #         if self.tax_label=='sr':
    #             self.label_description='Standard rated supplies with GST charged (0%)'
    #         elif self.tax_label=='st':
    #             self.label_description='SALE TAX 10%'
    #         elif self.tax_label=='su':
    #             self.label_description='Goods Own Used/Disposed 10%'
    #         elif self.tax_label=='st5':
    #             self.label_description='SALE TAX 5%'
    #         elif self.tax_label=='su5':
    #             self.label_description='Goods Own Used/Disposed 5%'
    #         elif self.tax_label=='suv':
    #             self.label_description='Service own used 6%'
    #         elif self.tax_label=='sv':
    #             self.label_description='Service Tax 6%'



class SSTTaxCode(models.Model):
    _name = 'account.tax.code'

    name=fields.Char('Code')
    des=fields.Char('Description')
