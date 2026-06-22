{
    'name': 'Sales Extend',
    'version': '19.1',
    'summary': 'Sale Extend ',
    'description': 'Description',
    'category': 'Category',
    'depends': ['sale_mrp'],
    'data': [
        'security/ir.model.access.csv',
        'wizard/mo_calc_wizard.xml',
        'views/sale_order.xml',
        'views/mo_calculation.xml',
        'views/mrp_bom_views.xml',
    ],
    'application': True,

}