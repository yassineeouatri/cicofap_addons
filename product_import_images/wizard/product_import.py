# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2019-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Mohammed Shahil MP @cybrosys(odoo@cybrosys.com)
#
#    You can modify it under the terms of the GNU AFFERO
#    GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
#    (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
import tempfile
import binascii
import base64
import certifi
import urllib3
import xlrd
from odoo.exceptions import Warning
from odoo import models, fields, _


class ProductImport(models.Model):

    _name = 'product.import'

    file = fields.Binary(string="Fichier")
    file_name = fields.Char(string="Nom du fichier")
    option = fields.Selection([('csv', 'CSV')], default='csv')

    def import_file(self):
        """ function to import product details from csv and xlsx file """
        if self.option == 'csv':
            try:
                product_temp_data = self.env['product.template'].search([])
                file = base64.b64decode(self.file)
                file_string = file.decode('utf-8')
                file_string = file_string.split('\n')
                http = urllib3.PoolManager(cert_reqs='CERT_REQUIRED',
                                           ca_certs=certifi.where())
            except:
                raise Warning(_("Please choose the correct file!"))

            firstline = True
            for file_item in file_string:
                if firstline:
                    firstline = False
                    continue
                product_temp = self.env['product.template'].search([('default_code', '=', file_item.split(",")[0])], limit=0)
                if product_temp.id:
                    if file_item.split(",")[0]:
                        if "http://" in file_item.split(",")[1] or "https://" in file_item.split(",")[1]:
                            link = file_item.split(",")[1]
                            image_response = http.request('GET', link)
                            image_thumbnail = base64.b64encode(image_response.data)
                            product_name = {
                                'default_code': file_item.split(",")[0],
                                'image_1920': image_thumbnail,
                            }
                            product_line = product_temp_data.write(product_name)
                        elif '//' in file_item.split(",")[1]:
                            with open(file_item.split(",")[1].strip(), 'rb') as file:
                                data = base64.b64encode(file.read())
                                product_name = {
                                    'default_code': file_item.split(",")[0],
                                    'image_1920': data,
                                }
                                product_temp = product_temp_data.write(product_name)
