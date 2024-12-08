# -*- coding: utf-8 -*-
{
    'name': 'Commercial User',
    'version': '1.0.0.0',
    'summary': 'Commercial User',
    'description': 'Create user from commercial',
    'category': '',
    'author': 'Yassine Elouatri',
    'website': 'https://rs-sa.com',
    'license': 'LGPL-3',
    'depends': ['base', 'cicofap'],
    'data': [
        'security/ir.model.access.csv',
        'views/product_commercial_view.xml',
        'wizard/product_commercial_user_view.xml'
    ],
    'installable': True,
    'auto_install': False,
}