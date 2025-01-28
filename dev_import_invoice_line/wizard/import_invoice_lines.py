# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2015 DevIntelle Consulting Service Pvt.Ltd (<http://www.devintellecs.com>).
#
#    For Module Support : devintelle@gmail.com  or Skype : devintelle
#
##############################################################################

from odoo import api, fields, models, _
import base64
import xlrd
from io import BytesIO
from xlwt import easyxf
from io import StringIO
import xlwt
import csv
from odoo.exceptions import ValidationError

class import_inventory_lines(models.TransientModel):
    _name = "import.invoice.lines"

    file_type = fields.Selection([('excel', 'Excel')],
                                 string='Type du fichier', default='excel')
    select_file = fields.Binary(string='Fichier')
    excel_file = fields.Binary(string='Télécharger un exemple de fichier', readonly=True)
    file_name = fields.Char('Nom du fichier', size=64)
    csv_file_name = fields.Char(string='Nom du fichier')
    import_by = fields.Selection(selection=[('internal_ref', 'Code')], default='internal_ref', required=True,
                                   string='Importer les produits par')

    def isfloat(self, num):
        try:
            if num.startswith('0'):
                return False
            float(num)
            return True
        except ValueError:
            return False

    def print_report(self):
        result = self.generate_excel_report()
        return result

    def _generate_csv_report(self):
        filename = 'Sample_Invoice.csv'
        csv_content = [
            ['Code', 'Description', 'Qty', 'Price'],
            ['5675', 'black-brown: Box', '1', '200'],
            ['1234', 'white Down', '2', '100']
        ]

        output = StringIO()
        writer = csv.writer(output)
        writer.writerows(csv_content)
        csv_string = output.getvalue()
        output.close()

        csv_file_data = csv_string.encode('utf-8')
        self.write({
            'excel_file': base64.encodebytes(csv_file_data),
            'file_name': filename
        })

        active_id = self.ids[0]
        return {
            'type': 'ir.actions.act_url',
            'url': f'web/content/?model=import.invoice.lines&download=true&field=excel_file&id={active_id}&filename={filename}',
            'target': 'new',
        }

    def generate_excel_report(self):
        filename = 'Exemple format.xls'
        workbook = xlwt.Workbook()
        worksheet = workbook.add_sheet('Line')
        worksheet.col(0).width = 4500
        worksheet.col(1).width = 4000
        worksheet.col(2).width = 4000
        worksheet.col(3).width = 4500
        worksheet.col(4).width = 4500
        font_style = easyxf(
            'font:height 215;pattern: pattern solid, fore_color gray25; font:bold True;align: vert center, horiz left;')

        worksheet.write(0, 0, 'Code',font_style)
        worksheet.write(0, 1, 'Qty',font_style)
        worksheet.write(0, 2, 'Prix',font_style)
        worksheet.write(0, 3, 'TVA', font_style)
        worksheet.write(0, 4, 'Remise', font_style)

        counter = 1
        worksheet.write(1, 0, '01M325429')
        worksheet.write(1, 1, '1')
        worksheet.write(1, 2, '200')
        worksheet.write(1, 3, 'TVA 20%')
        worksheet.write(1, 4, '0')

        counter = 1
        worksheet.write(2, 0, '01342')
        worksheet.write(2, 1, '2')
        worksheet.write(2, 2, '100')
        worksheet.write(2, 3, 'TVA 20%')
        worksheet.write(2, 4, '10')

        fp = BytesIO()
        workbook.save(fp)
        fp.seek(0)
        excel_file = base64.encodebytes(fp.read())
        fp.close()
        self.write({'excel_file': excel_file})
        active_id = self.ids[0]
        url = ('web/content/?model=import.invoice.lines&download=true&field=excel_file&id=%s&filename=%s' % (active_id, filename))
        if self.excel_file:
            return {'type': 'ir.actions.act_url',
                    'url': url,
                    'target': 'new'
                    }

    def import_line(self):
        active_id = self._context.get('active_id')
        move_id = self.env['account.move'].browse(active_id)
        
        if not self.select_file:
            raise ValidationError(_('No file uploaded!'))
        
        data = []
        file_data = base64.b64decode(self.select_file)

        if self.file_type == 'excel':
            try:
                workbook = xlrd.open_workbook(file_contents=file_data)
                sheet = workbook.sheet_by_index(0)
                data = [[sheet.cell_value(r, c) for c in range(sheet.ncols)] for r in range(sheet.nrows)]
                data.pop(0)
            except Exception:
                raise ValidationError(_('The uploaded file is not a valid Excel file.'))

        else:
            try:
                s_data = file_data.decode("utf-8").splitlines()
                data = [line.split(',') for line in s_data if line]
                data.pop(0)
            except Exception:
                raise ValidationError(_('The uploaded file is not a valid CSV file.'))
      
        count = 0
        note = ''
        for line in data:
            count += 1

            if self.import_by == 'name':
                domain = [('name', '=', line[0])]
            elif self.import_by == 'internal_ref':
                code = line[0]
                if self.isfloat(code):
                    if float(code) == int(float(code)):
                        code = str(int(float(code)))
                domain = [('default_code', '=', code)]
            else :
                domain = [('barcode', '=', str(line[0]))]

            product_id = self.env['product.product'].search(domain)

            tax_id_lst = []
            if line[3]:
                tax_names = line[3]
                tax = self.env['account.tax'].search([('name', '=', tax_names), ('type_tax_use', '=', 'sale')])
                if tax:
                    tax_id_lst.append(tax.id)

            if product_id:
                existing_line_ids = move_id.invoice_line_ids.filtered(
                    lambda l: l.product_id == product_id
                )
                if existing_line_ids:
                    for existing_line_id in existing_line_ids:
                        vals = [(1,existing_line_id.id,{
                            'quantity': existing_line_id.quantity+float(line[4]),
                        })]
                        move_id.invoice_line_ids = vals
                else:
                    vals = [(0,0,{
                    
                        'product_id': product_id.id or False,
                        'name': product_id.default_code or '',
                        'quantity': float(line[1]) or 0.0,
                        'price_unit': float(line[2]) or 0.0,
                        'product_uom_id': product_id and product_id.uom_id and product_id.uom_id.id,
                        'tax_ids': [(6, 0, tax_id_lst)],
                        'discount': float(line[4]) or 0.0
                    })]
                    move_id.invoice_line_ids = vals
            else:
                if not note:
                    note = "Produit non trouvé.\n"
                note += "Ligne N° :" + str(count) + " Produit :" + str(line[0]) + "\n"
        if note:
            log_id = self.env['invoice.log'].create({'name': note})
            return {
                'view_mode': 'form',
                'res_id': log_id.id,
                'res_model': 'invoice.log',
                'view_type': 'form',
                'type': 'ir.actions.act_window',
                'target': 'new',
            }

class sale_log(models.TransientModel):
    _name = "invoice.log"

    name = fields.Text(string='Logs',readonly=True)

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
