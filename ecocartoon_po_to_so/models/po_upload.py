# -*- coding: utf-8 -*-

from odoo import models, fields
from datetime import datetime
import requests
import base64
import io

import logging
_logger = logging.getLogger("LHDN")

class PortalPoUpload(models.Model):
    _name = 'portal.po.upload'
    _description = 'Portal PO Upload'
    _rec_name = 'name'
    _order = 'create_date desc'

    name = fields.Char(string='Reference',required=True,default='New PO Upload')
    partner_id = fields.Many2one('res.partner',string='Customer',readonly=True)
    uploaded_by = fields.Many2one('res.users',string='Uploaded By',default=lambda self: self.env.user,readonly=True)
    attachment_ids = fields.Many2many('ir.attachment','portal_po_upload_attachment_rel','upload_id','attachment_id',string='Uploaded Files')
    is_proceed = fields.Boolean(string='Processed',default=False)

    sale_order_id = fields.Many2one(
        'sale.order',
        string='Related Sale Order',
    )
    raw_payload = fields.Text(string="Raw Payload Data")
    remark = fields.Char(string="Remarks")

    def send_to_analyze_invoice(self, file):
        url = 'http://18.142.239.133:8765/pdf2json'

        base64_data = file.datas
        file_bytes = base64.b64decode(base64_data)
        file_obj = io.BytesIO(file_bytes)

        files = [
            ('file', (
                file.name,  # filename
                file_obj,  # file-like object
                'application/pdf'  # mime type
            ))
        ]

        # files = [('file', (file.filename, file.stream, file.content_type))]
        response = False
        try:
            # response = requests.post(url, files=files, timeout=40)
            response = requests.post(url, files=files)
            if response.status_code ==200:
                data = response.json()
                partner_name = data.get('Company').get('Name')
                partner_id = self.env['res.partner'].sudo().search([('name', '=',partner_name)],limit=1)
                # if not partner_id:
                #     partner_id = self.env['res.partner'].sudo().create({
                #         'name':partner_name,
                #         'street':data.get('Company').get('Address'),
                #         'phone':data.get('Company').get('Telephone'),
                #     })
                if partner_id:
                    date_str = data.get('OrderDate')
                    date_obj = datetime.strptime(date_str + ' 00:00:00', '%m/%d/%Y %H:%M:%S')

                    lines_dict = []
                    for line in data.get('Items'):
                        # product_id =
                        so_dict = {
                            'partner_id':partner_id,
                            'date_order':date_obj,
                            'order_line': [
                                (0, 0, {
                                    'product_id': product.id,
                                    'price_unit': product.list_price,
                                    'tax_id': None,
                                }) for product in products
                            ]
                        }
                else:
                    self.remark = "Customer name mismatched"

        except Exception as e:
            _logger.info(f"Errors gettings durings ans endpoints dataeas gettingyieas ==> {e}")
        # time.sleep(10)
        # return response


    def process_uploaded_po_pdf_ai(self):
        rec_ids = self.env['portal.po.upload'].sudo().search([],limit=5)
        for rec in rec_ids:
            rec.send_to_analyze_invoice(rec.attachment_ids)