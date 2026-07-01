# -*- coding: utf-8 -*-

import base64
from odoo import http
from odoo.http import request
from odoo.addons.portal.controllers.portal import CustomerPortal


class CustomerPortalTerms(CustomerPortal):

    def _prepare_home_portal_values(self, counters):
        values = super()._prepare_home_portal_values(counters)
        if 'po_count' in counters:
            values['po_count'] = 1
        return values

class PortalPoUploadController(http.Controller):

    @http.route('/my/po_upload', type='http', auth='user', website=True)
    def portal_po_upload_page(self, **kw):
        return request.render('ecocartoon_po_to_so.portal_po_upload_page',{})

    @http.route('/my/po_upload/submit',type='http',auth='user',methods=['POST'],website=True,csrf=True)
    def portal_po_upload_submit(self, **post):
        files = request.httprequest.files.getlist('po_files')
        for file in files:
            upload = request.env['portal.po.upload'].sudo().create({
                'name': file.filename,
                'partner_id': request.env.user.partner_id.id,
                'uploaded_by': request.env.user.id,
            })
            attachment = request.env['ir.attachment'].sudo().create({
                'name': file.filename,
                'datas': base64.b64encode(file.read()),
                'res_model': 'portal.po.upload',
                'res_id': upload.id,
                'mimetype': file.content_type,
            })
            upload.sudo().write({
                'attachment_ids': [(4, attachment.id)]
            })

        return request.redirect('/my')