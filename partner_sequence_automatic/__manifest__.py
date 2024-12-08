# -*- coding: utf-8 -*-
# module template
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    'name': 'Partner Sequence',
    'version': '15.0',
    'category': 'Base',
    'license': 'AGPL-3',
    'author': "Odoo Tips",
    'website': 'https://www.facebook.com/OdooTips/',
    'depends': ['base',
                ],

    'images': ['images/main_screenshot.png'],
    'data': [
             'views/res_partner_view.xml',
             'data/res_partner_sequence.xml',
             ],
    'installable': True,
    'application': True,
}
