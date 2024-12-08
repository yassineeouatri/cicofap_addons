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


    
class import_sp_line_wizard(models.TransientModel):
    _name='import.sp.line.wizard'
    _description = "Import Stock Picinkg Line"

    stock_picking_file=fields.Binary(string="Select File")
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
        try:
            fp = tempfile.NamedTemporaryFile(delete= False,suffix=".xlsx")
            fp.write(binascii.a2b_base64(self.stock_picking_file))
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
                values.update({
                    'code': code,
                    'received': line[1],
                })
                res = self.update_sp_line(values)
        return res

    def update_sp_line(self,values):
        stock_picking_brw=self.env['stock.picking'].browse(self._context.get('active_id'))
        current_time=datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        product=values.get('code')
        qty_done = values.get('received')

        if self.import_prod_option == 'code':
            product_obj_search=self.env['product.product'].search([('default_code', '=',values['code'])])
        else:
            product_obj_search=self.env['product.product'].search([('name', '=',values['code'])])

        if product_obj_search:
            product_id=product_obj_search[0]
            stock_picking_id = stock_picking_brw[0]
            stock_picking_line_search = self.env['stock.move'].search([('product_id', '=', product_id.id),
                                                                            ('picking_id', '=', stock_picking_id.id)])
            if stock_picking_line_search:
                stock_picking_line_search.write({'product_uom_qty': qty_done})
            else:
                if stock_picking_id.picking_type_id.default_location_src_id:
                    location_id = stock_picking_id.picking_type_id.default_location_src_id.id
                elif stock_picking_id.partner_id:
                    location_id = stock_picking_id.partner_id.property_stock_supplier.id
                else:
                    customerloc, location_id = stock_picking_id.env['stock.warehouse']._get_partner_locations()

                if stock_picking_id.picking_type_id.default_location_dest_id:
                    location_dest_id = stock_picking_id.picking_type_id.default_location_dest_id.id
                elif self.partner_id:
                    location_dest_id = stock_picking_id.partner_id.property_stock_customer.id
                else:
                    location_dest_id, supplierloc = self.env['stock.warehouse']._get_partner_locations()

                self.env['stock.move'].create({
                    'name': product_id.name,
                    'product_uom': 1,
                    'location_id': location_id,
                    'location_dest_id': location_dest_id,
                    #'location_id': stock_picking_id.picking_type_id.default_location_src_id.id,
                    'picking_id': stock_picking_id.id,
                    'product_id': product_id.id,
                    'product_uom_qty': qty_done
                })
        return True
        
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: