{
    'name': 'EcoCarton Extend',
    'version': '19.0.2.0.0',
    'category': 'Manufacturing',
    'summary': 'Create Transfer from Manufacturing Order',
    'depends': [
        'mrp','stock',
    ],
    'data': [
        'security/ir.model.access.csv',
        'data/product_data.xml',
        'wizards/ecocarton_transfer_wizard_views.xml',
        'views/mrp_production_views.xml',
        'views/mrp_bom_views.xml',
    ],
    'installable': True,
    'application': False,
}
