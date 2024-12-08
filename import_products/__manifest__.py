# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.
{
    'name': 'Import/Export/Search Products',
    'version': '15.0.0.0',
    'summary': 'Importer/exporter les produits',
    'category': 'Sales',
    "price": 9,
    "currency": 'EUR',
    'description': """
    """,
    'author': 'BrowseInfo',
    'website': '',
    
    'depends': ['base', 'cicofap'],
    'data': [   'security/security.xml',
                'security/ir.model.access.csv',
                'views/import_products_view.xml',
                'wizard/res_partner_merge_views.xml',
                'wizard/product_template_merge_views.xml',
            ],
    'demo': [],
    'test': [],
    'license':'OPL-1',
    'installable':True,
    'auto_install':False,
    'application':True,
    "images":['static/description/Banner.png'],
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
