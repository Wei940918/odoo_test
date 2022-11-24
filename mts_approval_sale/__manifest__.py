# -*- coding: utf-8 -*-
{
    'name': "mts_approval_sale",

    'summary': """
        Manage sales approval""",

    'description': """
        Manage sales approval
    """,

    'author': "My Company",
    'website': "http://www.yourcompany.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/12.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'sale', 'mail', 'crm'],
    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'security/ir.model.access.csv',
        'security/sale_approval_security.xml',
        'views/mail_templates.xml',
        'data/notification_data.xml',
        'views/sale.xml',
        'wizard/order_refused_reason_views.xml',
        'wizard/quotation_refused_reason_views.xml',
        'wizard/sale_closed_views.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}
