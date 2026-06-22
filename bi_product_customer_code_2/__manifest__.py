# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.
{
	'name': "Customer Products Code | Sale Product Code",
	'version': "19.0.0.1",
	'category': "Sales",
	'summary': 'Create Sale Product Code Manage Partner Product Code SO Client Product Code Sale Quotation Customer Code Sale Order Procdut Customer Code on Sales Order Apply Customer Code on Sales Unique Product Code Quotation Customer Product Internal Reference on Sale',
    'description' :"""

        Customer Products Code Odoo App helps users to show product-specific codes for a specific customer in the order line in the sale quotation/order and in the customer invoice. User can enable product customer code and enter product codes for specific customer. User can search product by their codes in sale quotation/order and customer invoice then use filter for customer product code and name also display customer product code in sale quotation/order and customer invoice report.

    """,
	'author': 'BROWSEINFO',
    'website': 'https://www.browseinfo.com/demo-request?app=bi_product_customer_code&version=18&edition=Community',
	'depends': ['base','sale_management','uom','account'],
	'data': [
				'security/ir.model.access.csv',
				'security/product_tags_security.xml',
				'views/product_cumstmor.xml',
                'views/res_config_settings_views.xml',
                'views/sale_order.xml',
                'report/report.xml',
			],
	'license':'OPL-1',
    'installable': True,
    'auto_install': False,
    'live_test_url':'https://www.browseinfo.com/demo-request?app=bi_product_customer_code&version=18&edition=Community',
    "images":['static/description/Products-Customer-Code.gif'],
}


