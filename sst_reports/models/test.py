from odoo import api, fields, models,_
from datetime import timedelta, date
from dateutil.relativedelta import relativedelta
from odoo.exceptions import ValidationError
import logging
_logger = logging.getLogger(__name__)



class sstcalcualtion(models.Model):
    _name = 'sst.cal'

    company_id=fields.Many2one('res.company','Registered Person',default=lambda self: self.env['res.company']._company_default_get('sst_reports'))
    name=fields.Char('Name',readonly=True)
    from_date=fields.Date('From')
    to_date=fields.Date('To')
    due_date=fields.Date('Due Date',readonly=True)
    state=fields.Selection([('draft','Draft'),('process','Processed')],default='draft')




    service_total=fields.Float('Total',compute='calculate_amt')
    service_net_total=fields.Float('Net Total',compute='calculate_amt')

    sst_service_ids=fields.One2many('sst.service.details','sst_id')
    sst_payable_ids=fields.One2many('sst.payable.goods','sst_payable_id')

    total_value_tax_payable_amt=fields.Float('Total Value of Tax Payable.')
    credit_note_tax=fields.Float('Tax Deducted from Credit Note')
    service_tax_deduction=fields.Float('Service Tax Deduction')
    total_tax_exclude_pen_amt=fields.Float('Total Tax Payable Before Penalty')

    penalty_rate=fields.Char('Penalty Rate',default='0%')
    penalty_amount=fields.Float('Penalty Amount',default='0.00')
    total_tax_include_pen_amt=fields.Float('Total of Tax Include Penalty')

    field_18_a=fields.Float('(18.A)Export / Special Area / Designated Area')
    field_18_b_1=fields.Float('(18.B.1)Schedule A (Class of Person).*')
    field_18_b_2=fields.Float('(18.B.2)Schedule B (Manufacturer of specific non taxa ble goods).*')
    field_18_b_3_1=fields.Float('(18.C.1)Item 1 and 2 (Purchase / Importation of Raw Material Exempted From Sales Tax).*')
    field_18_b_3_2=fields.Float('(18.C.2)Item 3 and 4 (Purchase / Importation of Raw Material on behalf of Registered Manufacturer Exempted From Sales Tax).*')
    field_18_b_3_3=fields.Float('(18.C.3)Item 5 (Value of Work Performed Exempted From Sales Tax).*')
    field_18_c=fields.Float('(18.C)Total Value of Exempted Taxable Services')


    field_19=fields.Float('(19)Item 1 and 2 (Purchase / Importation of Raw Material Exempted From Sales Tax).*')
    field_20=fields.Float('(20)Item 3 and 4 (Purchase / Importation of Raw Material on behalf of Registered Manufacturer Exempted From Sales Tax).')
    field_21=fields.Float('(21)Item 5 (Value of Work Performed Exempted From Sales Tax).*')

    def print_sst(self):
        # data = {}
        # data['form'] = {
        #     'date_from': self.from_date,
        #     'date_to': self.to_date,
        #     'company_id': self.company_id.id,
        #     'doc_ids':self,
        # }
        # final_dict = {}
        # final_dict.update(data)
        return self.env.ref('sst_reports.action_report_account_sst').report_action(self)

    def get_from_date_digit(self,i,f):
        print('column no',i)
        date_time_from = self.from_date.strftime("%d%m%Y")
        if date_time_from:
            if i==0 and f==f:
                return date_time_from[0]
            if i==1 and f==f:
                return date_time_from[1]
            if i==2 and f==f:
                return date_time_from[2]
            if i==3 and f==f:
                return date_time_from[3]
            if i==4 and f==f:
                return date_time_from[4]
            if i==5 and f==f:
                return date_time_from[5]


    def get_to_date_digit(self, i, t):
        date_time_to = self.to_date.strftime("%d%m%Y")
        if date_time_to:
            if i == 0 and t == t:
                return date_time_to[0]
            if i == 1 and t == t:
                return date_time_to[1]
            if i == 2 and t == t:
                return date_time_to[2]
            if i == 3 and t == t:
                return date_time_to[3]
            if i == 4 and t == t:
                return date_time_to[4]
            if i == 5 and t == t:
                return date_time_to[5]

    def get_due_date_digit(self,i,d):
        date_time_due=self.due_date.strftime("%d%m%Y")
        if date_time_due:
            if i == 0 and d == d:
                return date_time_due[0]
            if i == 1 and d == d:
                return date_time_due[1]
            if i == 2 and d == d:
                return date_time_due[2]
            if i == 3 and d == d:
                return date_time_due[3]
            if i == 4 and d == d:
                return date_time_due[4]
            if i == 5 and d == d:
                return date_time_due[5]

    def get_current_date_digit(self, i, d):
        date_time_due = (date.today()).strftime("%d%m%Y")
        if date_time_due:
            if i == 0 and d == d:
                return date_time_due[0]
            if i == 1 and d == d:
                return date_time_due[1]
            if i == 2 and d == d:
                return date_time_due[2]
            if i == 3 and d == d:
                return date_time_due[3]
            if i == 4 and d == d:
                return date_time_due[4]
            if i == 5 and d == d:
                return date_time_due[5]

    def sum_sale_total(self):
        result=sum([r.subtotal for r in self.sst_service_ids])
        return result
    def sum_service_total(self):
        result = sum([r.free_service for r in self.sst_service_ids])
        return result
    def sum_total(self):
        result = sum([r.total for r in self.sst_service_ids])
        return result





    @api.model
    def create(self,vals):
        res=super(sstcalcualtion,self).create(vals)
        from_date=res.from_date.strftime("%d %B %Y")
        end_date=res.to_date.strftime("%d %B %Y")
        res.name='SST Return - '+from_date+' to '+end_date
        return res

    @api.onchange('from_date', 'to_date')
    def chnage_field_values(self):
        print('onchange')
        self.sst_service_ids.unlink()
        self.sst_payable_ids.unlink()
        if self.from_date and self.to_date:
            self.due_date = self.to_date+relativedelta(months=1)
            from_date = self.from_date.strftime("%d %B %Y")
            end_date = self.to_date.strftime("%d %B %Y")
            self.name = 'SST Return - ' + from_date + ' to ' + end_date

    def generate_values(self):
        print('generate_values')
        self.due_date=self.to_date+relativedelta(months=1)
        self.calculate_sst_service_lines()
        self.calculate_part_d()
        self.calculate_part_e()
        self.calculate_amt()



    def calculate_sst_service_lines(self):
        print('calculate_sst_service_lines')
        
        #creating service lines
        hs_code_obj=self.env['hs.code'].search([])
        number=1
        if self.state=='process':
            raise ValidationError('SST Alredy Processsed.modification is not possible')
        else:
            for hs_code in hs_code_obj:
                account_move_line_obj=self.env['account.move.line'].search([('move_id.invoice_date','>=',self.from_date),('move_id.invoice_date','<=',self.to_date),
                                                        ('move_id.state','=','posted'),('product_id.hs_code','=',hs_code.id),('move_id.type','=','out_invoice')])
                print(len(account_move_line_obj))
                _logger.info("=====================invoices line======%s"%account_move_line_obj)
                good_sold_amt=0
                own_sold_amt=0
                for line in account_move_line_obj:
                    if line.tax_ids:
                        _logger.info("=====================invoicess======%s"%line.move_id.name)
                        for tax in line.tax_ids:
                            if tax.tax_code_id.name in ['SU-10','SU-5']:
                                # own_sold_amt+=(line.quantity*line.price_unit)
                                own_sold_amt+=line.price_subtotal
                            if tax.tax_code_id.name in ['S-10','S-5']:
                                # good_sold_amt+=(line.quantity*line.price_unit)
                                good_sold_amt+=(line.price_subtotal)
                            else:
                               _logger.info("=====================first else======") 
                            pass
                    else:pass            

                print('good_sold_amt',good_sold_amt)
                print('own_sold_amt',own_sold_amt)
                service_vals={'tariff_code':hs_code.name,'subtotal':round(good_sold_amt,2),'description':hs_code.description,'number':number,
                              'sst_id':self.id or self.active_id.id,'free_service':round(own_sold_amt,2)}
                print('len',len(self.sst_service_ids),len(self.sst_payable_ids))
                c=self.sst_service_ids.create(service_vals)

                number+=1
            hs_code_obj_new_list=[]
            hs_code_obj_new=self.env['hs.code'].search([])
            for hs_code in hs_code_obj_new:
                hs_code_obj_new_list.append(hs_code.name)

            #creating sst paable lines
            payable_list = []
            account_move_line_obj_payable= self.env['account.move.line'].search(
                [('move_id.invoice_date', '>=', self.from_date), ('move_id.invoice_date', '<=', self.to_date),
                 ('move_id.state', '=', 'posted'),('move_id.type', 'in', ['out_invoice']),('product_id.hs_code','in',hs_code_obj_new_list)])
            print(len(account_move_line_obj_payable))
            tax_five_percentage_amt=0
            tax_ten_percetnage_amt=0
            for line in account_move_line_obj_payable:
                if line.tax_ids:
                    for tax in line.tax_ids:
                        if tax.tax_code_id.name in ['SU-5', 'S-5']:
                            tax_five_percentage_amt += (line.price_subtotal)
                        elif tax.tax_code_id.name in ['SU-10','S-10']:
                            tax_ten_percetnage_amt += (line.price_subtotal)
                else:pass            
            value_taxable_sales_amt_five=tax_five_percentage_amt
            value_taxable_sales_amt_ten=tax_ten_percetnage_amt
            payable_list.append([0, 0, {'label': 'Taxable Good at 5% Rate', 'value_taxable_sales_amt': value_taxable_sales_amt_five,
                                        'tax_rate': '5%', 'tax_payable_amt': (value_taxable_sales_amt_five*0.05)}])
            payable_list.append(
                [0, 0, {'label': 'Taxable Good at 10% Rate', 'value_taxable_sales_amt': value_taxable_sales_amt_ten,
                        'tax_rate': '10%', 'tax_payable_amt': (value_taxable_sales_amt_ten * 0.10)}])

            payable_list.append([0, 0, {'label': 'Taxable service other than from group H', 'value_taxable_sales_amt': 0.0,
                                        'tax_rate': '6%', 'tax_payable_amt': 0.0}])
            self.write({'sst_payable_ids': payable_list})
            self.total_value_tax_payable_amt = sum([(line.tax_payable_amt) for line in self.sst_payable_ids])
            cn_account_line_obj = account_move_line_obj = self.env['account.move.line'].search(
                [('move_id.invoice_date', '>=', self.from_date), ('move_id.invoice_date', '<=', self.to_date),
                 ('move_id.state', '=', 'posted'), ('move_id.type', 'in', ['out_refund'])])
            cn_result = sum([(line.price_total - line.price_subtotal) for line in cn_account_line_obj])

            print('cn', cn_account_line_obj, cn_result)
            if len(cn_account_line_obj) > 0 and cn_result != 0:
                self.credit_note_tax = cn_result
            else:
                pass
            self.total_tax_exclude_pen_amt = self.total_value_tax_payable_amt - self.credit_note_tax

    def calculate_part_d(self):
        print('calculate_part_d',self.from_date,self.to_date)
        account_move_line_obj = self.env['account.move.line'].search(
            [('move_id.invoice_date', '>=', self.from_date), ('move_id.invoice_date', '<=', self.to_date),
             ('move_id.state', '=', 'posted'),
             ('move_id.type', 'in', ['out_invoice']),('account_internal_type','=','other')])
        field_18_a_total=0
        field_18_b1_total=field_18_b2_total=field_18_b31_total=field_18_b32_total=field_18_b33_total=field_18_c_total=0
        for move_line in account_move_line_obj:
            if move_line.tax_ids.tax_code_id.name in ['EEM','ESP','EDA']:
                field_18_a_total=field_18_a_total+(move_line.credit)
            if move_line.tax_ids.tax_code_id.name=='ESA':
                field_18_b1_total=field_18_b1_total+(move_line.price_subtotal)
            if move_line.tax_ids.tax_code_id.name == 'ESB':
                field_18_b2_total = field_18_b2_total + (move_line.price_subtotal)
            if move_line.tax_ids.tax_code_id.name=='ESC-A':
                field_18_b31_total=field_18_b31_total+(move_line.price_subtotal)
            if move_line.tax_ids.tax_code_id.name == 'ESC-B':
                field_18_b32_total = field_18_b32_total + (move_line.price_subtotal)
            if move_line.tax_ids.tax_code_id.name == 'ESC-C':
                field_18_b33_total = field_18_b33_total + (move_line.price_subtotal)
            if move_line.tax_ids.tax_code_id.name == 'ESV-6':
                field_18_c_total = field_18_c_total + (move_line.price_subtotal)

        self.field_18_a=field_18_a_total
        self.field_18_b_1=field_18_b1_total
        self.field_18_b_2=field_18_b2_total
        self.field_18_b_3_1=field_18_b31_total
        self.field_18_b_3_2=field_18_b32_total
        self.field_18_b_3_3=field_18_b33_total
        self.field_18_c=field_18_c_total





    def calculate_part_e(self):
        print('calculate_part_e',self.from_date,self.to_date)
        account_move_line_obj = self.env['account.move.line'].search(
            [('move_id.invoice_date', '>=', self.from_date),('move_id.invoice_date', '<=', self.to_date),
             ('move_id.state', '=', 'posted'),
             ('move_id.type', 'in', ['in_invoice'])])
        field_19_total=0
        field_20_total=0
        field_21_total=0
        for move_line in account_move_line_obj:
            if move_line.tax_ids.tax_code_id.name=='EPC-A':
                field_19_total=field_19_total+(move_line.price_subtotal)
            if move_line.tax_ids.tax_code_id.name=='EPC-B':
                field_20_total=field_20_total+(move_line.price_subtotal)
            if move_line.tax_ids.tax_code_id.name=='EPC-C':
                field_21_total=field_21_total+(move_line.price_subtotal)
        self.field_19=field_19_total
        self.field_20=field_20_total
        self.field_21=field_21_total



    def calculate_amt(self):
        print('compute_amt')
        total_goods_sold=sum([line.subtotal for line in self.sst_service_ids])
        own_used_total=sum([line.free_service for line in self.sst_service_ids])
        taxable_service_total=sum([line.total for line in self.sst_service_ids])
        print(total_goods_sold,own_used_total,taxable_service_total)
        net_total=total_goods_sold+own_used_total+taxable_service_total
        print(net_total)
        self.service_net_total=net_total

    def clear(self):
        if self.state=='draft':
            self.sst_service_ids.unlink()
            self.sst_payable_ids.unlink()
            self.service_net_total=0
            self.tax_payable_amt=0
            self.total_value_tax_payable_amt=0
            self.credit_note_tax=0
            self.total_tax_exclude_pen_amt=0
            self.field_18_a=0
            self.field_18_b_1=0
            self.field_18_b_2=0
            self.field_18_b_3_1=0
            self.field_18_b_3_2=0
            self.field_18_b_3_3=0
            self.field_18_c=0
            self.field_19=0
            self.field_20=0
            self.field_21=0
        else:
            raise ValidationError('Modification not possible')

    def process(self):
        if self.due_date:
            today = date.today()
            if self.due_date<today<(self.due_date+timedelta(days=30)):
                print('first if')
                self.penalty_rate='10%'
                self.penalty_amount=self.total_tax_exclude_pen_amt*(0.10)
                self.total_tax_include_pen_amt=self.total_tax_exclude_pen_amt+self.penalty_amount
            elif self.due_date<today<(self.due_date+timedelta(days=60)):
                print('second if')
                self.penalty_rate='25%'
                self.penalty_amount=self.total_tax_exclude_pen_amt*(0.25)
                self.total_tax_include_pen_amt=self.total_tax_exclude_pen_amt+self.penalty_amount

            elif self.due_date<today<(self.due_date+timedelta(days=90)):
                print('third if')
                self.penalty_rate='40%'
                self.penalty_amount=self.total_tax_exclude_pen_amt*(0.40)
                self.total_tax_include_pen_amt=self.total_tax_exclude_pen_amt+self.penalty_amount

            elif today>(self.due_date+timedelta(days=90)):
                print('fourth if')
                self.penalty_rate='40%'
                self.penalty_amount=self.total_tax_exclude_pen_amt*(0.40)
                self.total_tax_include_pen_amt=self.total_tax_exclude_pen_amt+self.penalty_amount
            else:
                print('else')
                self.penalty_rate='0%'
                self.penalty_amount=0
                self.total_tax_include_pen_amt=self.total_tax_exclude_pen_amt+self.penalty_amount
        self.state='process'

class sstservicedetails(models.Model):
    _name = 'sst.service.details'

    sst_id=fields.Many2one('sst.cal')
    number=fields.Char('Bil No.')
    description=fields.Char('Description of Taxable Goods / Type of Taxable Service Provided/Imported*')
    tariff_code=fields.Char('Customs Tariff Code / Service Type Code.*')
    subtotal=fields.Float('Value of Taxable Goods Sold (Including Value of Debit Note) /Disposed Value of Work Performed. *')
    free_service=fields.Float('Value of Goods For Own Used /Debit Note) /Disposed')
    total=fields.Float('Value of Taxable Service(Including Value of Debit Note)*')

class sstpayablegoods(models.Model):
    _name = 'sst.payable.goods'

    sst_payable_id=fields.Many2one('sst.cal')
    label=fields.Char('Label')
    value_taxable_sales_amt=fields.Float('Value of Taxable Sales / Service')
    tax_rate=fields.Char('Tax Rate')
    tax_payable_amt=fields.Float('Value of Tax Payble')

class sstaccountmove(models.Model):
    _inherit = 'account.move'

    def action_post(self):
        res=super(sstaccountmove, self).action_post()
        print(self.invoice_date)
        sst_ret_obj=self.env['sst.cal'].search([('state','=','process')])
        for record in sst_ret_obj:
            print(record)
            if record.from_date and record.to_date and self.invoice_date:
                if record.from_date<=self.invoice_date<record.to_date:
                    txt='{} already processed ,posting is not allowed'
                    raise ValidationError(txt.format(record.name))
                else:pass
        return res






