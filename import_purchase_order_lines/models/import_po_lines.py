# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _ ,exceptions
from datetime import datetime
from odoo.exceptions import Warning
import binascii
import tempfile
from tempfile import TemporaryFile
from odoo.exceptions import UserError, ValidationError
import logging
from odoo.tools import ustr
_logger = logging.getLogger(__name__)
import io

try:
    import xlrd
except ImportError:
    _logger.debug('Cannot `import xlrd`.')
try:
    import csv
except ImportError:
    _logger.debug('Cannot `import csv`.')
try:
    import base64
except ImportError:
    _logger.debug('Cannot `import base64`.')


    
class import_po_line_wizard(models.TransientModel):
    _name='import.po.line.wizard'
    _description = "Import Purchase Order Line"

    purchase_order_file=fields.Binary(string="Select File")
    import_option = fields.Selection([('xls', 'XLS File')],string='Select',default='xls')
    import_prod_option = fields.Selection([('code', 'Code'),('name', 'Name')],string='Import Product By ',default='code')
    product_details_option = fields.Selection([('from_xls','Take Details From The XLS/CSV File')],default='from_xls')

    def isfloat(self, num):
        try:
            float(num)
            return True
        except ValueError:
            return False

    def import_pol(self):
        if self.import_option == 'csv':
            keys = ['code', 'quantity', 'uom','description', 'price', 'tax']
            try:
                csv_data = base64.b64decode(self.purchase_order_file)
                data_file = io.StringIO(csv_data.decode("utf-8"))
                data_file.seek(0)
                file_reader = []
                csv_reader = csv.reader(data_file, delimiter=',')
                file_reader.extend(csv_reader)
            except Exception:
                raise exceptions.ValidationError(_("Invalid file!"))
            values = {}
            for i in range(len(file_reader)):
                field = list(map(str, file_reader[i]))
                values = dict(zip(keys, field))
                if values:
                    if i == 0:
                        continue
                    else:
                        res = self.create_po_line(values)
        else:
            try:
                fp = tempfile.NamedTemporaryFile(delete= False,suffix=".xlsx")
                fp.write(binascii.a2b_base64(self.purchase_order_file))
                fp.seek(0)
                values = {}
                workbook = xlrd.open_workbook(fp.name)
                sheet = workbook.sheet_by_index(0)
            except Exception:
                raise exceptions.ValidationError(_("Invalid file!"))

            product_obj = self.env['product.product']
            for row_no in range(sheet.nrows):
                val = {}
                if row_no <= 0:
                    fields = map(lambda row:row.value.encode('utf-8'), sheet.row(row_no))
                else:
                    line = list(map(lambda row:isinstance(row.value, bytes) and row.value.encode('utf-8') or ustr(row.value), sheet.row(row_no)))
                    code = line[0]

                    if self.isfloat(code):
                        if float(code) == int(float(code)):
                            code = str(int(float(code)))
                    if self.product_details_option == 'from_product':
                        values.update({
                                'code' : code,
                                'quantity' : line[1]
                        })
                    elif self.product_details_option == 'from_xls':
                        values.update({
                           'code': code,
                           'quantity':line[1],
                           'uom':line[2],
                           'price':line[3],
                           'tax':line[4],
                             })
                    else:
                        values.update({
                                        'code' : code,
                                        'quantity' : line[1],
                                    })                        

                    res = self.create_po_line(values)
        return res

    def create_po_line(self,values):
        purchase_order_brw=self.env['purchase.order'].browse(self._context.get('active_id'))
        current_time=datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        product=values.get('code')
        if self.product_details_option == 'from_product':
            if self.import_prod_option == 'barcode':
              product_obj_search=self.env['product.product'].search([('barcode',  '=',values['code'])])
            elif self.import_prod_option == 'code':
                product_obj_search=self.env['product.product'].search([('default_code', '=',values['code'])])
            else:
                product_obj_search=self.env['product.product'].search([('name', '=',values['code'])])
    
            if product_obj_search:
                product_id=product_obj_search[0]
            else:
                raise ValidationError(_('%s product is not found".') % values.get('code'))

            if purchase_order_brw.state == 'draft':
                po_order_lines=self.env['purchase.order.line'].create({
                                                    'order_id':purchase_order_brw.id,
                                                    'product_id':product_id.id,
                                                    'name':product_id.name,
                                                    'date_planned':current_time,
                                                    'product_qty':values.get('quantity'),
                                                    'product_uom':product_id.uom_po_id.id,
                                                    'price_unit':product_id.standard_price
                                                    })
                
            elif purchase_order_brw.state == 'sent':
                po_order_lines=self.env['purchase.order.line'].create({
                                                    'order_id':purchase_order_brw.id,
                                                    'product_id':product_id.id,
                                                    'name':product_id.name,
                                                    'date_planned':current_time,
                                                    'product_qty':values.get('quantity'),
                                                    'product_uom':product_id.uom_po_id.id,
                                                    'price_unit':product_id.standard_price
                                                    })

            elif purchase_order_brw.state != 'sent' or purchase_order_brw.state != 'draft':
                raise UserError(_('We cannot import data in validated or confirmed order.'))

        elif self.product_details_option == 'from_xls':
            uom=values.get('uom')
            if self.import_prod_option == 'barcode':
              product_obj_search=self.env['product.product'].search([('barcode',  '=',values['code'])])
            elif self.import_prod_option == 'code':
                product_obj_search=self.env['product.product'].search([('default_code', '=',values['code'])])
            else:
                product_obj_search=self.env['product.product'].search([('name', '=',values['code'])])

            uom_obj_search=self.env['uom.uom'].search([('name','=',uom)])
            tax_id_lst=[]
            if values.get('tax'):
                if ';' in values.get('tax'):
                    tax_names = values.get('tax').split(';')
                    for name in tax_names:
                        tax = self.env['account.tax'].search([('name', '=', name), ('type_tax_use', '=', 'purchase')])
                        if not tax:
                            raise ValidationError(_('"%s" Tax not in your system') % name)
                        tax_id_lst.append(tax.id)

                elif ',' in values.get('tax'):
                    tax_names = values.get('tax').split(',')
                    for name in tax_names:
                        tax = self.env['account.tax'].search([('name', '=', name), ('type_tax_use', '=', 'purchase')])
                        if not tax:
                            raise ValidationError(_('"%s" Tax not in your system') % name)
                        tax_id_lst.append(tax.id)
                else:
                    tax_names = values.get('tax').split(',')
                    tax = self.env['account.tax'].search([('name', '=', tax_names), ('type_tax_use', '=', 'purchase')])
                    if not tax:
                        raise ValidationError(_('"%s" Tax not in your system') % tax_names)
                    tax_id_lst.append(tax.id)
            if not uom_obj_search:
                raise ValidationError(_('UOM "%s" is Not Available') % uom)

            if product_obj_search:
                product_id=product_obj_search[0]
            else:
                if self.import_prod_option == 'name':
                    if values.get('price'):
                        standard_price = float(values.get('price'))
                    else:
                        standard_price = False

                    product_id=self.env['product.product'].create({'name':product,'standard_price':standard_price})
                else:
                    raise ValidationError(_('%s product is not found" .\n If you want to create product then first select Import Product By Name option .') % values.get('code'))
            
            if values.get('quantity'):
                quantity = float(values.get('quantity'))
            else:
                quantity = False

            if purchase_order_brw.state == 'draft':
                if values.get('price'):
                    standard_price = float(values.get('price'))
                else:
                    standard_price = False
                po_order_lines=self.env['purchase.order.line'].create({
                                                    'order_id':purchase_order_brw.id,
                                                    'product_id':product_id.id,
                                                    'name':product_id.name,
                                                    'date_planned':current_time,
                                                    'product_qty':quantity,
                                                    'product_uom':uom_obj_search.id or False,
                                                    'price_unit':standard_price
                                                    })
                

            elif purchase_order_brw.state == 'sent':
                po_order_lines=self.env['purchase.order.line'].create({
                                                    'order_id':purchase_order_brw.id,
                                                    'product_id':product_id.id,
                                                    'name':product_id.name,
                                                    'date_planned':current_time,
                                                    'product_qty':quantity,
                                                    'product_uom':uom_obj_search.id or False,
                                                    'price_unit':(values.get('price'))
                                                    })

            elif purchase_order_brw.state != 'sent' or purchase_order_brw.state != 'draft':
                raise UserError(_('We cannot import data in validated or confirmed order.'))
            if tax_id_lst:
                po_order_lines.write({'taxes_id':([(6,0,tax_id_lst)])})
        else:
            if self.import_prod_option == 'barcode':
              product_obj_search=self.env['product.product'].search([('barcode',  '=',values['code'])])
            elif self.import_prod_option == 'code':
                product_obj_search=self.env['product.product'].search([('default_code', '=',values['code'])])
            else:
                product_obj_search=self.env['product.product'].search([('name', '=',values['code'])])

            if product_obj_search:
                product_id=product_obj_search[0]
            else:
                if self.import_prod_option == 'name':
                    if values.get('price'):
                        standard_price = float(values.get('price'))
                    else:
                        standard_price = False
                    product_id=self.env['product.product'].create({'name':product,'standard_price':standard_price})
                else:
                    raise ValidationError(_('%s product is not found" .\n If you want to create product then first select Import Product By Name option .') % values.get('code'))
            
            if values.get('quantity'):
                quantity = float(values.get('quantity'))
            else:
                quantity = False

            if purchase_order_brw.state == 'draft':
                po_order_lines=self.env['purchase.order.line'].create({
                                                    'order_id':purchase_order_brw.id,
                                                    'product_id':product_id.id,
                                                    'name':values['code'],
                                                    'date_planned':current_time,
                                                    'product_qty':quantity,
                                                    'product_uom':product_id.uom_po_id.id,
                                                    'price_unit':product_id.standard_price
                                                    })
                po_order_lines.onchange_product_id() 
                po_order_lines.update({
                                    'product_qty':values.get('quantity'),
                    })                                                   
                                                        
            elif purchase_order_brw.state == 'sent':
                po_order_lines=self.env['purchase.order.line'].create({
                                                    'order_id':purchase_order_brw.id,
                                                    'product_id':product_id.id,
                                                    'name':values['code'],
                                                    'date_planned':current_time,
                                                    'product_qty':quantity,
                                                    'product_uom':product_id.uom_po_id.id,
                                                    'price_unit':product_id.standard_price
                                                    })
                po_order_lines.onchange_product_id() 
                po_order_lines.update({
                                    'product_qty':values.get('quantity'),
                    }) 

            elif purchase_order_brw.state != 'sent' or purchase_order_brw.state != 'draft':
                raise UserError(_('We cannot import data in validated or confirmed order.'))              
        return True
        
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: