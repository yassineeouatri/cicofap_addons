# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'Cicofap Module',
    'version': '1.0',
    'description': """
        Odoo Cicofap custum module.
        ===========================
        
        This module customize all modules
        """,
    'depends': [
        'web',
        'account',
        'product',
        'stock',
        'purchase',
        'sale',
        'bi_sales_security',
        'bispro_partner_filter',
        'sale_stock_CICOFAP',
        'hspl_image_importer'
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
    'data': [
        'security/account_security.xml',
        'security/ir.model.access.csv',
        'data/ir_sequence_data.xml',
        'views/product.xml',
        'views/account.xml',
        'views/stock.xml',
        'views/purchase.xml',
        'wizard/sale_make_invoice_cash_views.xml',
        'wizard/invoice_cash_payment_register_views.xml',
        'views/sale.xml',
        'views/report_invoice.xml',
        'views/report_deliveryslip.xml',
        'views/product_movement.xml',
        'views/sale_report_template.xml',
        'views/partner.xml',
        'views/sms.xml',
        'views/invoice_cash_views.xml',
        'wizard/sale_order_print_views.xml',
        'report/sale_order_report.xml',
        #'views/template.xml',
        'views/menus.xml'
    ],
    'assets': {
        'web.assets_backend': [
            'cicofap/static/**/*',
        ],
    },
    'license': 'LGPL-3',
}
