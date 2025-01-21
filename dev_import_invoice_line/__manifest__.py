# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2015 DevIntelle Consulting Service Pvt.Ltd (<http://www.devintellecs.com>).
#
#    For Module Support : devintelle@gmail.com  or Skype : devintelle
#
##############################################################################

{
    'name': 'Import Invoice Lines | Import Account Move Lines',
    'version': '15.0.1.0',
    'sequence': 1,
    'category': 'Account',
    'description':
        """
Import Invoice Lines Odoo app simplifies the process of importing invoice lines using CSV or Excel files. This app allows users to efficiently add invoice line details by product name, internal reference, or barcode, streamlining invoice management and reducing manual data entry efforts. With a user-friendly interface, users can upload their files, and the app validates the file type to ensure it matches the selected format (CSV or Excel). If there is a mismatch, a validation message is displayed, helping to avoid errors. Once uploaded, the imported invoice lines are displayed for review, and the files can be easily downloaded for reference or record-keeping.
    """,
    'summary': 'Import Invoice Line import account move lines import move lines import csv import excel import invoice csv import invoice excel import invoice lie csv import invoice lne excel all in one import lines all in one import csv all in one import excel',
    'depends': ['base', 'account'],
    'data': [
        'security/ir.model.access.csv',
        'wizard/import_invoice_lines_view.xml',
        'views/invoice_view.xml',
        
    ],
	'demo': [],
    'test': [],
    'css': [],
    'qweb': [],
    'js': [],
    'images': ['images/main_screenshot.gif'],
    'installable': True,
    'application': True,
    'auto_install': False,
    
    #author and support Details
    'author': 'DevIntelle Consulting Service Pvt.Ltd',
    'website': 'http://www.devintellecs.com',    
    'maintainer': 'DevIntelle Consulting Service Pvt.Ltd', 
    'support': 'devintelle@gmail.com',
    'price':11.0,
    'currency':'EUR',
    #'live_test_url':'https://youtu.be/A5kEBboAh_k',
    'pre_init_hook' :'pre_init_check',
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
