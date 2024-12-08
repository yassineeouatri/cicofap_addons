# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'Gestion des ventes et entrepôts CICOFAP',
    'version': '1.0',
    'category': 'Hidden',
    'summary': 'Quotation, Sales Orders, Delivery & Invoicing Control',
    'description': """
Manage sales quotations and orders
==================================

This module makes the link between the sales and warehouses management applications.

Preferences
-----------
* Shipping: Choice of delivery at once or partial delivery
* Invoicing: choose how invoices will be paid
* Incoterms: International Commercial terms

""",
    'depends': ['sale_stock'],
    'data': [
        'views/sale_order_views.xml',
    ],
    'demo': [],
    'installable': True,
    'auto_install': False,
    'assets': {},
    'license': 'LGPL-3',
}