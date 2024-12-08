# -*- coding: utf-8 -*-
{
    'name': 'Partner Solde',
    'version': '1.0.0.0',
    'summary': 'Partner Solde',
    'description': 'Add Partner Solde, and make it available to search with',
    'category': '',
    'author': 'Yassine Elouatri',
    'website': 'https://rs-sa.com',
    'license': 'LGPL-3',
    'depends': ['base'],
    'data': [
        'security/ir.model.access.csv',
        'views/res_partner_view.xml',
        'wizard/res_partner_user_view.xml'
    ],
    'installable': True,
    'auto_install': False,
}