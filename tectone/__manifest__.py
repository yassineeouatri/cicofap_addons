# -*- encoding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
{
    'name': 'Tectone Production',
    'version': '3.0',
    'category': '',
    'description': """
    """,
    "author" : "Yassine Elouatri",
    'summary': 'Tectone Production Module',
    'website': '',
    'depends': ['base_setup', 'base', 'mail'],
    'data': [
        'security/account_security.xml',
        'security/ir.model.access.csv',
        'data/production.xml',
        'data/production_bordereau_sequence.xml',
        'views/affaire.xml',
        'views/report.xml',
        'views/production.xml',
        'wizard/production_indice_add_view.xml',
        'wizard/production_file_add_view.xml',
        'wizard/production_document_send_view.xml',
        'wizard/production_pointage_add_view.xml',
        'wizard/production_report_view.xml',
    ],
    'demo': [
    ],
    'installable': True,
    'auto_install': False,
    'application': True,
    'sequence': 105,
    'license': 'LGPL-3',
}
