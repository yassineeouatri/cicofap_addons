# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.
{
    'name': 'Import Stock Picking Lines from Excel or CSV File in odoo',
    'version': '15.0.0.0',
    'summary': 'Import purchase order line Data App for import purchase order lines import purchases data import PO line excel import purchase order line from excel import purchase order line from csv import mass purchase order import bulk purchase order line import',
    'description': """
	-
    """,
    'author': 'BrowseInfo',
    'website': 'https://www.browseinfo.in',
    'depends': ['base','stock'],
    'data': [   
                'security/ir.model.access.csv',
                'views/import_sp_lines_view.xml'
            ],
    'demo': [],
    'test': [],
    'license':'OPL-1',
    'installable':True,
    'auto_install':False,
    'application':True,
    'live_test_url':'https://youtu.be/VpiAemvzcpI',
    "images":['static/description/Banner.png'],
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
