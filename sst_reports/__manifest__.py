{
    'name': 'SST Reports',
    'version': '19.1',
    'author': "Precomp"
              ,
    'summary':'',
    'website': '',
    'license': 'AGPL-3',
    'category': 'account',
    'depends': [
        'base','account', 'product_field_hs_code'
    ],
    'data': [
        'reports/layout.xml',
        'reports/sst_report_template.xml',
        'reports/reports.xml',
        'views/view.xml',
        'security/ir.model.access.csv',
        'views/view_inherits.xml',
        'data/data.xml'
    ],
    'auto_install': False,
    'installable': True,
}