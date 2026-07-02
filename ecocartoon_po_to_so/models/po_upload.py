# -*- coding: utf-8 -*-

from odoo import models, fields
from datetime import datetime
import requests
import base64
import json
import io

import logging

_logger = logging.getLogger("LHDN")


class PortalPoUpload(models.Model):
    _name = 'portal.po.upload'
    _description = 'Portal PO Upload'
    _rec_name = 'name'
    _order = 'create_date desc'

    name = fields.Char(string='Reference', required=True, default='New PO Upload')
    partner_id = fields.Many2one('res.partner', string='Customer', readonly=True)
    uploaded_by = fields.Many2one('res.users', string='Uploaded By', default=lambda self: self.env.user, readonly=True)
    attachment_ids = fields.Many2many('ir.attachment', 'portal_po_upload_attachment_rel', 'upload_id', 'attachment_id',
                                      string='Uploaded Files')
    is_proceed = fields.Boolean(string='Processed', default=False)

    sale_order_id = fields.Many2one(
        'sale.order',
        string='Related Sale Order',
    )
    raw_payload = fields.Text(string="Raw Payload Data")
    remark = fields.Char(string="Remarks")

    def send_to_analyze_invoice(self, file):
        url = 'http://18.142.239.133:8765/pdf2json'
        text2json_url = 'http://18.142.239.133:8765/odoo_text2json'
        base64_data = file.datas
        file_bytes = base64.b64decode(base64_data)
        file_obj = io.BytesIO(file_bytes)
        _logger.info(f"{file.name} ==> file starting to processings")
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
            if response.status_code == 200:
                data = response.json()
                _logger.info(f"{file.name} ==> pdf to json raw data converting step 1 is done")
                # Step 3: Create .json file dynamically (in memory)
                json_string = json.dumps(data, indent=2)  # Pretty print with indent
                json_bytes = json_string.encode('utf-8')
                json_file_obj = io.BytesIO(json_bytes)

                # Step 4: Send to text_2_json API with same format
                files_for_text = [
                    ('file', (
                        'output.json',  # Dynamic filename
                        json_file_obj,  # JSON file object
                        'application/json'  # MIME type
                    ))
                ]

                text_response = requests.post(text2json_url, files=files_for_text)
                data = text_response.json()
                data = data[0]
                _logger.info(f"{file.name} ==> json raw to json data converting step 2 is done")
                self.raw_payload = data
                partner_name = data.get('partner_id').get('name')
                partner_id = self.env['res.partner'].sudo().search([('name', '=', partner_name)], limit=1)
                # if not partner_id:
                #     partner_id = self.env['res.partner'].sudo().create({
                #         'name':partner_name,
                #         'street':data.get('Company').get('Address'),
                #         'phone':data.get('Company').get('Telephone'),
                #     })
                if partner_id:
                    date_str = data.get('invoice_date')

                    date_obj = datetime.strptime(date_str + ' 00:00:00', '%Y-%m-%d %H:%M:%S') if date_str else False

                    lines_dict = []
                    # product_lines_dict = []
                    product_found_in_odoo = True
                    for line in data.get('move_line'):
                        product_code = line.get('product_id').get('name')
                        product_id = self.env['product.customer.code'].search(
                            [('product_code', '=', product_code), ('name_id.id', '=', partner_id.id)], limit=1)
                        if product_id:
                            product_id = product_id.product_id
                            lines_dict.append((0, 0, {
                                'product_id': product_id.id,
                                'price_unit': line.get('price_unit'),
                                'product_uom_qty': line.get('quantity')
                            }))
                        else:
                            self.remark = f"Product not found intos the odoo system ==>{product_code}"
                            product_found_in_odoo = False
                            break
                    if product_found_in_odoo:
                        so_dict = {
                            'partner_id': partner_id.id,
                            'date_order': date_obj if date_obj else False,
                            'order_line': lines_dict
                        }
                        self.env['sale.order'].sudo().create(so_dict)
                        self.is_proceed = True
                else:
                    self.remark = "Customer name mismatched"

        except Exception as e:
            self.remark = f"error gettings ==>{e}"
            _logger.info(f"Errors gettings durings ans endpoints dataeas gettingyieas ==> {e}")
        # time.sleep(10)
        # return response

    def process_uploaded_po_pdf_ai(self):
        rec_ids = self.env['portal.po.upload'].sudo().search([('is_proceed','=',False)], limit=5)
        for rec in rec_ids:
            rec.send_to_analyze_invoice(rec.attachment_ids)
