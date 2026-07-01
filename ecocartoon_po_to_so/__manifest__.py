# -*- coding: utf-8 -*-

{
    'name': 'Ecocartoon PO To SO',
    'version': '19.0.1.0.0',
    'category': 'Portal',
    'summary': 'Portal PO Upload',
    'author': 'Ecocartoon',
    'depends': ['portal', 'website', 'sale'],
    'data': [
        'security/ir.model.access.csv',
        'views/portal_templates.xml',
        'views/po_upload_views.xml',
        'data/ir_cron.xml',
    ],
    'installable': True,
    'application': False,
}
