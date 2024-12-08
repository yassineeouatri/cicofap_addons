# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.exceptions import Warning, ValidationError
import binascii
import tempfile
import xlrd
from tempfile import TemporaryFile
from odoo.exceptions import UserError
import xlsxwriter
import logging
import time
_logger = logging.getLogger(__name__)
import io
import requests
from os.path import exists

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

class product_template_wizard(models.TransientModel):
    _name='product.template.wizard'
    _description = "Product template Wizard"

    search_value = fields.Char('Valeur recherchée')
    product_template_file=fields.Binary(string="Select File")
    import_option = fields.Selection([('xls', 'XLS File')],string='Select',default='xls')
    import_prod_option = fields.Selection([('code', 'Code'),('name', 'Name')],string='Import Product By ',default='code')
    product_details_option = fields.Selection([('from_xls','Take Details From The XLS File')],default='from_xls')

    def isfloat(self, num):
        try:
            float(num)
            return True
        except ValueError:
            return False

    def is_integer(self, string):
        """Checks if a string represents an integer.

        Args:
            string: The string to check.

        Returns:
            True if the string is an integer, False otherwise.
        """

        try:
            int(string)
            return True
        except ValueError:
            return False

    def get_value(self, value):
        if 'E' not in value:
            if self.isfloat(value):
                if float(value) == int(float(value)):
                    value = str(int(float(value)))
        return value

    def create_attribute_line(self, product_template_id, attribute_id, attribute_value_id):
        product_template_attribute_line_obj_search = self.env['product.template.attribute.line'].search([
            ('product_tmpl_id', '=', product_template_id.id),
            ('attribute_id', '=', attribute_id.id)
        ])
        if product_template_attribute_line_obj_search:
            product_template_attribute_line_obj_search.unlink()
        self.env['product.template.attribute.line'].create({'product_tmpl_id': product_template_id.id,
                                                            'attribute_id': attribute_id.id,
                                                            'value_ids': [(4, attribute_value_id.id)]})
        return True

    def import_sol(self):
        res = False
        try:
            fp = tempfile.NamedTemporaryFile(delete= False,suffix=".xlsx")
            fp.write(binascii.a2b_base64(self.product_template_file))
            fp.seek(0)
            values = {}
            workbook = xlrd.open_workbook(fp.name)
            sheet = workbook.sheet_by_index(0)
        except Exception as e:
            raise ValidationError(_(e))

        for row_no in range(sheet.nrows):
            val = {}
            if row_no <= 0:
                fields = list(map(lambda row:isinstance(row.value, bytes) and row.value.encode('utf-8') or str(row.value), sheet.row(row_no)))
            else:
                line = list(map(lambda row:isinstance(row.value, bytes) and row.value.encode('utf-8') or str(row.value), sheet.row(row_no)))
                line_dict = {}
                for i in range(len(line)):
                    line_dict[fields[i]] = line[i]
                print(line_dict)
                category = ''
                if 'category' in line_dict:
                    category = line_dict.get('category', '').strip()
                ss_category = ''
                if 'subcategory' in line_dict:
                    ss_category = line_dict.get('subcategory', '').strip()
                code = ''
                if 'code' in line_dict:
                    code = line_dict.get('code', '').strip()
                    code = self.get_value(code)
                name = ''
                if 'designation' in line_dict:
                    name = line_dict.get('designation', '').strip()
                marque_voiture = ''
                if 'marque' in line_dict:
                    marque_voiture = line_dict.get('marque', '').strip()
                oem = ''
                if 'oem' in line_dict:
                    oem = line_dict.get('oem', '').strip()
                    oem = self.get_value(oem)
                cross = ''
                if 'cross' in line_dict:
                    cross = line_dict.get('cross', '').strip()
                    cross = self.get_value(cross)
                compatibilities = ''
                if 'compatibilities' in line_dict:
                    compatibilities = line_dict.get('compatibilities', '').strip()
                    compatibilities = self.get_value(compatibilities)
                type1 = ''
                if 'type' in line_dict:
                    type1 = line_dict.get('type', '').strip()
                dimension = ''
                if 'dimension' in line_dict:
                    dimension = line_dict.get('dimension', '').strip()
                poids = ''
                if 'weight' in line_dict:
                    poids = line_dict.get('weight', '').strip()
                    poids = self.get_value(poids)
                hauteur = ''
                if 'height' in line_dict:
                    hauteur = line_dict.get('height', '').strip()
                    hauteur = self.get_value(hauteur)
                largeur = ''
                if 'width' in line_dict:
                    largeur = line_dict.get('width', '').strip()
                    largeur = self.get_value(largeur)
                epaisseur = ''
                if 'thickness' in line_dict:
                    epaisseur = line_dict.get('thickness', '').strip()
                    epaisseur = self.get_value(epaisseur)
                dent = ''
                if 'dent' in line_dict:
                    dent = line_dict.get('dent', '').strip()
                    dent = self.get_value(dent)
                model = ''
                if 'model' in line_dict:
                    model = line_dict.get('model', '').strip()
                    model = self.get_value(model)
                direction = ''
                if 'direction' in line_dict:
                    direction = line_dict.get('direction', '').strip()
                    direction = self.get_value(direction)
                materiel = ''
                if 'materiel' in line_dict:
                    materiel = line_dict.get('materiel', '').strip()
                    materiel = self.get_value(materiel)
                cote = ''
                if 'cote' in line_dict:
                    cote = line_dict.get('cote', '').strip()
                    cote = self.get_value(cote)
                filetage = ''
                if 'filetage' in line_dict:
                    filetage = line_dict.get('filetage', '').strip()
                    filetage = self.get_value(filetage)
                cout = ''
                if 'cout' in line_dict:
                    cout = line_dict.get('cout', '').replace(',', '.').replace(' ', '')
                sale_price = ''
                if 'sale_price' in line_dict:
                    sale_price = line_dict.get('sale_price', '').replace(',', '.').replace(' ', '')
                tva = ''
                if 'tva' in line_dict:
                    tva = line_dict.get('tva', '')
                supplier = ''
                if 'supplier' in line_dict:
                    supplier = line_dict.get('supplier', '')
                ref_supplier = ''
                if 'ref_supplier' in line_dict:
                    ref_supplier = line_dict.get('ref_supplier', '')
                    ref_supplier = self.get_value(ref_supplier)
                purchase_price = 0
                if 'purchase_price' in line_dict:
                    purchase_price = line_dict.get('purchase_price', 0)
                devise_achat = ''
                if 'devise_achat' in line_dict:
                    devise_achat = line_dict.get('devise_achat', '')
                category_id = None
                if category:
                    category_obj_search = self.env['product.category'].search([('name', '=', category)])
                    if category_obj_search:
                        category_id = category_obj_search
                    else:
                        category_id = self.env['product.category'].create({'name': category})
                if ss_category:
                    category_obj_search = self.env['product.category'].search([('name', '=', ss_category)])
                    if category_obj_search:
                        category_id = category_obj_search
                    else:
                        if category_id:
                            category_id = self.env['product.category'].create({'name': ss_category, 'parent_id': category_id.id})
                        else:
                            category_id = self.env['product.category'].create({'name': ss_category})
                marque_id = None
                if marque_voiture:
                    marque_obj_search = self.env['product.marque'].search([('name', '=', marque_voiture)])
                    if marque_obj_search:
                        marque_id = marque_obj_search
                    else:
                        marque_id = self.env['product.marque'].create({'name': marque_voiture})

                    marque_attribute_id, marque_attribute_value_id = self.get_attributes('Marque de voiture', marque_voiture)
                supplier_id = None
                if supplier:
                    supplier = supplier.upper()
                    supplier_obj_search = self.env['res.partner'].search([('name', '=', supplier)], limit=1)
                    if supplier_obj_search:
                        supplier_id = supplier_obj_search
                    else:
                        supplier_id = self.env['res.partner'].create({'name': supplier})
                if code:
                    product_obj_search = self.env['product.product'].search([('default_code', '=', code)])
                    payload = {'detailed_type': 'product'}
                    payload['default_code'] = code
                    if name:
                        payload['name'] = name
                    if category_id:
                        payload['categ_id'] = category_id.id
                    if marque_id:
                        payload['marque_id'] = marque_id.id
                    if supplier_id:
                        payload['supplier_id'] = supplier_id.id
                    if sale_price:
                        payload['list_price'] = float(sale_price)
                    if cout:
                        payload['standard_price'] = float(cout)

                    if product_obj_search:
                        _logger.info('update')
                        product_id = product_obj_search
                        product_id.write(payload)
                    else:
                        _logger.info('create')
                        if name:
                            product_id = self.env['product.product'].create(payload)
                    product_template_id = None
                    product_template_obj_search = self.env['product.template'].search([('default_code', '=', code)])
                    if product_template_obj_search:
                        product_template_id = product_template_obj_search[0]
                    self._cr.execute("select id from account_tax where type_tax_use='sale' and description like '%20%'")
                    for row in self._cr.fetchall():
                        tax_id = row[0]
                    if product_template_id:
                        self._cr.execute("insert into product_taxes_rel(prod_id,tax_id) "
                                         " values( {},{}) on conflict (prod_id,tax_id) do nothing;".format(product_template_id.id, tax_id))
                        if compatibilities:
                            self._cr.execute(
                                "delete from product_template_compatibility where template_id={}".format(product_template_id.id))
                            compatibilities = compatibilities.split('\n')
                            for compatibilty in compatibilities:
                                self.env['product.template.compatibility'].create({'template_id': product_template_id.id, 'name': compatibilty})
                        if marque_voiture:
                            self.create_attribute_line(product_template_id, marque_attribute_id, marque_attribute_value_id)
                        if supplier:
                            if not purchase_price:
                                purchase_price = 0

                            if devise_achat:
                                currency_obj_search = self.env['res.currency'].search([('name', '=', devise_achat)])
                                if currency_obj_search:
                                    currency_id = currency_obj_search
                                else:
                                    currency_id = self.env['res.currency'].search([('name', '=', 'MAD')])
                            else:
                                currency_id = self.env['res.currency'].search([('name', '=', 'MAD')])

                            product_supplier_obj_search = self.env['product.supplierinfo'].search([('product_tmpl_id', '=', product_template_id.id),
                                                                                                   ('name', '=', supplier_id.id)])
                            if product_supplier_obj_search:
                                product_supplier_id = product_supplier_obj_search
                                product_supplier_id.write({'product_code': ref_supplier,
                                                           'price': float(purchase_price),
                                                           'currency_id': currency_id.id})
                            else:
                                product_supplier_id = self.env['product.supplierinfo'].create({'product_tmpl_id': product_template_id.id,
                                                                                               'name':supplier_id.id,
                                                                                               'product_code': ref_supplier,
                                                                                               'price': purchase_price,
                                                                                               'currency_id': currency_id.id
                                                                                               })
                        if oem:
                            oem_attribute_id, oem_attribute_value_id = self.get_attributes('OEM',oem)
                            self.create_attribute_line(product_template_id, oem_attribute_id, oem_attribute_value_id)
                        if cross:
                            cross_attribute_id, cross_attribute_value_id = self.get_attributes('CROSS',cross)
                            self.create_attribute_line(product_template_id, cross_attribute_id, cross_attribute_value_id)
                        if dimension:
                            dimension_attribute_id, dimension_attribute_value_id = self.get_attributes('Dimension', dimension)
                            self.create_attribute_line(product_template_id, dimension_attribute_id, dimension_attribute_value_id)
                        if type1:
                            type_attribute_id, type_attribute_value_id = self.get_attributes('Type', type1)
                            self.create_attribute_line(product_template_id, type_attribute_id, type_attribute_value_id)
                        if poids:
                            poids_attribute_id, poids_attribute_value_id = self.get_attributes('Poids', poids)
                            self.create_attribute_line(product_template_id, poids_attribute_id, poids_attribute_value_id)
                        if hauteur:
                            hauteur_attribute_id, hauteur_attribute_value_id = self.get_attributes('Hauteur', hauteur)
                            self.create_attribute_line(product_template_id, hauteur_attribute_id, hauteur_attribute_value_id)
                        if largeur:
                            largeur_attribute_id, largeur_attribute_value_id = self.get_attributes('Largeur', largeur)
                            self.create_attribute_line(product_template_id, largeur_attribute_id, largeur_attribute_value_id)
                        if epaisseur:
                            self.create_attribute_line(product_template_id, epaisseur_attribute_id, epaisseur_attribute_value_id)
                            epaisseur_attribute_id, epaisseur_attribute_value_id = self.get_attributes('Epaisseur', epaisseur)
                        if dent:
                            dent_attribute_id, dent_attribute_value_id = self.get_attributes('Nombre de dents', dent)
                            self.create_attribute_line(product_template_id, dent_attribute_id, dent_attribute_value_id)
                        if model:
                            model_attribute_id, model_attribute_value_id = self.get_attributes('Modèle', model)
                            self.create_attribute_line(product_template_id, model_attribute_id, model_attribute_value_id)
                        if direction:
                            direction_attribute_id, direction_attribute_value_id = self.get_attributes('Direction', direction)
                            self.create_attribute_line(product_template_id, direction_attribute_id, direction_attribute_value_id)
                        if materiel:
                            materiel_attribute_id, materiel_attribute_value_id = self.get_attributes('Matériel', materiel)
                            self.create_attribute_line(product_template_id, materiel_attribute_id, materiel_attribute_value_id)
                        if cote:
                            cote_attribute_id, cote_attribute_value_id = self.get_attributes('Côté', cote)
                            self.create_attribute_line(product_template_id, cote_attribute_id, cote_attribute_value_id)
                        if filetage:
                            filetage_attribute_id, filetage_attribute_value_id = self.get_attributes('Filetage', filetage)
                            self.create_attribute_line(product_template_id, filetage_attribute_id, filetage_attribute_value_id)
        return res

    def import_compatibility(self):
        try:
            fp = tempfile.NamedTemporaryFile(delete= False,suffix=".xlsx")
            fp.write(binascii.a2b_base64(self.product_template_file))
            fp.seek(0)
            values = {}
            workbook = xlrd.open_workbook(fp.name)
            sheet = workbook.sheet_by_index(0)
        except Exception as e:
            raise ValidationError(_(e))

        for row_no in range(sheet.nrows):
            val = {}
            if row_no <= 0:
                fields = list(map(lambda row:isinstance(row.value, bytes) and row.value.encode('utf-8') or str(row.value), sheet.row(row_no)))
            else:
                line = list(map(lambda row:isinstance(row.value, bytes) and row.value.encode('utf-8') or str(row.value), sheet.row(row_no)))
                line_dict = {}
                for i in range(len(line)):
                    line_dict[fields[i]] = line[i]
                product_template_id = None
                if 'CODE' in line_dict:
                    code = line_dict.get('CODE', '').strip()
                    code = self.get_value(code)
                    print(code)
                    product_template_obj_search = self.env['product.template'].search([('default_code', '=', code)])
                    if product_template_obj_search:
                        product_template_id = product_template_obj_search
                print(product_template_id)
                if product_template_id and product_template_id is not None:
                    payload = {'template_id': product_template_id.id}

                    manufacturer_id = None
                    if 'MANUFACTURER' in line_dict:
                        manufacturer = line_dict.get('MANUFACTURER', '').strip()
                        if manufacturer:
                            manufacturer_obj_search = self.env['product.manufacturer'].search([('name', '=', manufacturer)], limit=1)
                            if manufacturer_obj_search:
                                manufacturer_id = manufacturer_obj_search
                            else:
                                manufacturer_id = self.env['product.manufacturer'].create({'name': manufacturer})
                    if manufacturer_id:
                        payload['manufacturer_id'] = manufacturer_id.id

                    model_id = None
                    if 'MODEL' in line_dict:
                        model = line_dict.get('MODEL', '').strip()
                        if model:
                            model_obj_search = self.env['product.manufacturer.model'].search([('name', '=', model)], limit=1)
                            if model_obj_search:
                                model_id = model_obj_search
                            else:
                                model_id = self.env['product.manufacturer.model'].create({'name': model})
                    if model_id:
                        payload['model_id'] = model_id.id

                    serie_id = None
                    if 'MODEL SERIE' in line_dict:
                        serie = line_dict.get('MODEL SERIE', '').strip()
                        if serie:
                            serie_obj_search = self.env['product.manufacturer.serie'].search([('name', '=', serie)], limit=1)
                            if serie_obj_search:
                                serie_id = serie_obj_search
                            else:
                                serie_id = self.env['product.manufacturer.serie'].create({'name': serie})
                    if serie_id:
                        payload['serie_id'] = serie_id.id

                    engine_type_id = None
                    if 'ENGINE TYPE' in line_dict:
                        engine_type = line_dict.get('ENGINE TYPE', '').strip()
                        if engine_type:
                            engine_type_obj_search = self.env['product.engine.type'].search([('name', '=', engine_type)],
                                                                                             limit=1)
                            if engine_type_obj_search:
                                engine_type_id = engine_type_obj_search
                            else:
                                engine_type_id = self.env['product.engine.type'].create({'name': engine_type})
                    if engine_type_id:
                        payload['engine_type_id'] = engine_type_id.id

                    drive_type_id = None
                    if 'DRIVE TYPE' in line_dict:
                        drive_type = line_dict.get('DRIVE TYPE', '').strip()
                        if drive_type:
                            drive_type_obj_search = self.env['product.drive.type'].search([('name', '=', drive_type)],
                                                                                            limit=1)
                            if drive_type_obj_search:
                                drive_type_id = drive_type_obj_search
                            else:
                                drive_type_id = self.env['product.drive.type'].create({'name': drive_type})
                    if drive_type_id:
                        payload['drive_type_id'] = drive_type_id.id

                    body_type_id = None
                    if 'BODY TYPE' in line_dict:
                        body_type = line_dict.get('BODY TYPE', '').strip()
                        print(body_type)
                        if body_type:
                            body_type_obj_search = self.env['product.body.type'].search([('name', '=', body_type)],
                                                                                          limit=1)
                            if body_type_obj_search:
                                body_type_id = body_type_obj_search
                            else:
                                body_type_id = self.env['product.body.type'].create({'name': body_type})
                    if body_type_id:
                        payload['body_type_id'] = body_type_id.id
                        print(body_type_id.id)

                    motor_type_id = None
                    if 'MOTOR TYPE' in line_dict:
                        motor_type = line_dict.get('MOTOR TYPE', '').strip()
                        if motor_type:
                            motor_type_obj_search = self.env['product.motor.type'].search([('name', '=', motor_type)],
                                                                                        limit=1)
                            if motor_type_obj_search:
                                motor_type_id = motor_type_obj_search
                            else:
                                motor_type_id = self.env['product.motor.type'].create({'name': motor_type})
                    if motor_type_id:
                        payload['motor_type_id'] = motor_type_id.id

                    kw = -1
                    if 'KW' in line_dict:
                        kw_found = line_dict.get('KW', 0).strip()
                        if self.isfloat(kw_found):
                            kw = int(float(kw_found))
                    if kw > 0:
                        payload['kw'] = kw

                    hp = -1
                    if 'HP' in line_dict:
                        hp_found = line_dict.get('HP', 0).strip()
                        if self.isfloat(hp_found):
                            hp = int(float(hp_found))
                    if hp > 0:
                        payload['hp'] = hp

                    cylinder = -1
                    if 'CYLINDER' in line_dict:
                        cylinder_found = line_dict.get('CYLINDER', 0).strip()
                        if self.isfloat(cylinder_found):
                            cylinder = int(float(cylinder_found))
                    if cylinder > 0:
                        payload['cylinder'] = cylinder

                    valve = -1
                    if 'VALVE' in line_dict:
                        valve_found = line_dict.get('VALVE', 0).strip()
                        if self.isfloat(valve_found):
                            valve = int(float(valve_found))
                    if valve > 0:
                        payload['valve'] = valve

                    engine_code = None
                    if 'ENGINE CODE' in line_dict:
                        engine_code = line_dict.get('ENGINE CODE', '').strip()
                    if engine_code:
                        payload['engine_code'] = engine_code

                    model_year = None
                    if 'MODEL YEAR' in line_dict:
                        model_year = line_dict.get('MODEL YEAR', '').strip()
                    if model_year:
                        payload['model_year'] = model_year

                    self.env['product.template.compatibility'].create(payload)

        return True

    def import_products(self):
        res = False
        try:
            file_path = "C://Users//Yassine//Downloads//products.xls"
            file_path = "/home/bitnami/products.xls"
            workbook = xlrd.open_workbook(file_path)
            sheet = workbook.sheet_by_index(0)
        except Exception as e:
            raise ValidationError(_(e))

        for row_no in range(sheet.nrows):
            val = {}
            if row_no <= 0:
                fields = list(map(lambda row:isinstance(row.value, bytes) and row.value.encode('utf-8') or str(row.value), sheet.row(row_no)))
            else:
                line = list(map(lambda row:isinstance(row.value, bytes) and row.value.encode('utf-8') or str(row.value), sheet.row(row_no)))
                line_dict = {}
                for i in range(len(line)):
                    line_dict[fields[i]] = line[i]
                print(line_dict)
                category = ''
                if 'category' in line_dict:
                    category = line_dict.get('category', '').strip()
                ss_category = ''
                if 'subcategory' in line_dict:
                    ss_category = line_dict.get('subcategory', '').strip()
                code = ''
                if 'code' in line_dict:
                    code = line_dict.get('code', '').strip()
                    code = self.get_value(code)
                name = ''
                if 'designation' in line_dict:
                    name = line_dict.get('designation', '').strip()
                marque_voiture = ''
                if 'marque' in line_dict:
                    marque_voiture = line_dict.get('marque', '').strip()
                oem = ''
                if 'oem' in line_dict:
                    oem = line_dict.get('oem', '').strip()
                    oem = self.get_value(oem)
                cross = ''
                if 'cross' in line_dict:
                    cross = line_dict.get('cross', '').strip()
                    cross = self.get_value(cross)
                compatibilities = ''
                if 'compatibilities' in line_dict:
                    compatibilities = line_dict.get('compatibilities', '').strip()
                    compatibilities = self.get_value(compatibilities)
                type1 = ''
                if 'type' in line_dict:
                    type1 = line_dict.get('type', '').strip()
                dimension = ''
                if 'dimension' in line_dict:
                    dimension = line_dict.get('dimension', '').strip()
                poids = ''
                if 'weight' in line_dict:
                    poids = line_dict.get('weight', '').strip()
                    poids = self.get_value(poids)
                hauteur = ''
                if 'height' in line_dict:
                    hauteur = line_dict.get('height', '').strip()
                    hauteur = self.get_value(hauteur)
                largeur = ''
                if 'width' in line_dict:
                    largeur = line_dict.get('width', '').strip()
                    largeur = self.get_value(largeur)
                epaisseur = ''
                if 'thickness' in line_dict:
                    epaisseur = line_dict.get('thickness', '').strip()
                    epaisseur = self.get_value(epaisseur)
                dent = ''
                if 'dent' in line_dict:
                    dent = line_dict.get('dent', '').strip()
                    dent = self.get_value(dent)
                model = ''
                if 'model' in line_dict:
                    model = line_dict.get('model', '').strip()
                    model = self.get_value(model)
                direction = ''
                if 'direction' in line_dict:
                    direction = line_dict.get('direction', '').strip()
                    direction = self.get_value(direction)
                materiel = ''
                if 'materiel' in line_dict:
                    materiel = line_dict.get('materiel', '').strip()
                    materiel = self.get_value(materiel)
                cote = ''
                if 'cote' in line_dict:
                    cote = line_dict.get('cote', '').strip()
                    cote = self.get_value(cote)
                filetage = ''
                if 'filetage' in line_dict:
                    filetage = line_dict.get('filetage', '').strip()
                    filetage = self.get_value(filetage)
                cout = ''
                if 'cout' in line_dict:
                    cout = line_dict.get('cout', '')
                sale_price = ''
                if 'sale_price' in line_dict:
                    sale_price = line_dict.get('sale_price', '')
                tva = ''
                if 'tva' in line_dict:
                    tva = line_dict.get('tva', '')
                supplier = ''
                if 'supplier' in line_dict:
                    supplier = line_dict.get('supplier', '')
                ref_supplier = ''
                if 'ref_supplier' in line_dict:
                    ref_supplier = line_dict.get('ref_supplier', '')
                    ref_supplier = self.get_value(ref_supplier)
                purchase_price = 0
                if 'purchase_price' in line_dict:
                    purchase_price = line_dict.get('purchase_price', 0)
                devise_achat = ''
                if 'devise_achat' in line_dict:
                    devise_achat = line_dict.get('devise_achat', '')
                category_id = None
                if category:
                    category_obj_search = self.env['product.category'].search([('name', '=', category)])
                    if category_obj_search:
                        category_id = category_obj_search
                    else:
                        category_id = self.env['product.category'].create({'name': category})
                if ss_category:
                    category_obj_search = self.env['product.category'].search([('name', '=', ss_category)])
                    if category_obj_search:
                        category_id = category_obj_search
                    else:
                        if category_id:
                            category_id = self.env['product.category'].create({'name': ss_category, 'parent_id': category_id.id})
                        else:
                            category_id = self.env['product.category'].create({'name': ss_category})
                marque_id = None
                if marque_voiture:
                    marque_obj_search = self.env['product.marque'].search([('name', '=', marque_voiture)])
                    if marque_obj_search:
                        marque_id = marque_obj_search
                    else:
                        marque_id = self.env['product.marque'].create({'name': marque_voiture})

                    marque_attribute_id, marque_attribute_value_id = self.get_attributes('Marque de voiture', marque_voiture)
                supplier_id = None
                if supplier:
                    supplier = supplier.upper()
                    supplier_obj_search = self.env['res.partner'].search([('name', '=', supplier)], limit=1)
                    if supplier_obj_search:
                        supplier_id = supplier_obj_search
                    else:
                        supplier_id = self.env['res.partner'].create({'name': supplier})
                if code:
                    product_obj_search = self.env['product.product'].search([('default_code', '=', code)])
                    payload = {'detailed_type': 'product'}
                    payload['default_code'] = code
                    if name:
                        payload['name'] = name
                    if category_id:
                        payload['categ_id'] = category_id.id
                    if marque_id:
                        payload['marque_id'] = marque_id.id
                    if supplier_id:
                        payload['supplier_id'] = supplier_id.id
                    if sale_price:
                        payload['list_price'] = float(sale_price)
                    if cout:
                        payload['standard_price'] = float(cout)

                    if product_obj_search:
                        _logger.info('update')
                        product_id = product_obj_search
                        product_id.write(payload)
                    else:
                        _logger.info('create')
                        if name:
                            product_id = self.env['product.product'].create(payload)
                    product_template_id = None
                    product_template_obj_search = self.env['product.template'].search([('default_code', '=', code)])
                    if product_template_obj_search:
                        product_template_id = product_template_obj_search
                    self._cr.execute("select id from account_tax where type_tax_use='sale' and description like '%20%'")
                    for row in self._cr.fetchall():
                        tax_id = row[0]
                    if product_template_id:
                        print(product_template_id)
                        self._cr.execute("insert into product_taxes_rel(prod_id,tax_id) "
                                         " values( {},{}) on conflict (prod_id,tax_id) do nothing;".format(product_template_id.id, tax_id))
                        if compatibilities:
                            self._cr.execute(
                                "delete from product_template_compatibility where template_id={}".format(product_template_id.id))
                            compatibilities = compatibilities.split('\n')
                            for compatibilty in compatibilities:
                                self.env['product.template.compatibility'].create({'template_id': product_template_id.id, 'name': compatibilty})
                        if marque_voiture:
                            self.create_attribute_line(product_template_id, marque_attribute_id, marque_attribute_value_id)
                        if supplier:
                            if not purchase_price:
                                purchase_price = 0

                            if devise_achat:
                                currency_obj_search = self.env['res.currency'].search([('name', '=', devise_achat)])
                                if currency_obj_search:
                                    currency_id = currency_obj_search
                                else:
                                    currency_id = self.env['res.currency'].search([('name', '=', 'MAD')])
                            else:
                                currency_id = self.env['res.currency'].search([('name', '=', 'MAD')])

                            product_supplier_obj_search = self.env['product.supplierinfo'].search([('product_tmpl_id', '=', product_template_id.id),
                                                                                                   ('name', '=', supplier_id.id)])
                            if product_supplier_obj_search:
                                product_supplier_id = product_supplier_obj_search
                                product_supplier_id.write({'product_code': ref_supplier,
                                                           'price': float(purchase_price),
                                                           'currency_id': currency_id.id})
                            else:
                                product_supplier_id = self.env['product.supplierinfo'].create({'product_tmpl_id': product_template_id.id,
                                                                                               'name':supplier_id.id,
                                                                                               'product_code': ref_supplier,
                                                                                               'price': purchase_price,
                                                                                               'currency_id': currency_id.id
                                                                                               })
                        if oem:
                            oem_attribute_id, oem_attribute_value_id = self.get_attributes('OEM',oem)
                            self.create_attribute_line(product_template_id, oem_attribute_id, oem_attribute_value_id)
                        if cross:
                            cross_attribute_id, cross_attribute_value_id = self.get_attributes('CROSS',cross)
                            self.create_attribute_line(product_template_id, cross_attribute_id, cross_attribute_value_id)
                        if dimension:
                            dimension_attribute_id, dimension_attribute_value_id = self.get_attributes('Dimension', dimension)
                            self.create_attribute_line(product_template_id, dimension_attribute_id, dimension_attribute_value_id)
                        if type1:
                            type_attribute_id, type_attribute_value_id = self.get_attributes('Type', type1)
                            self.create_attribute_line(product_template_id, type_attribute_id, type_attribute_value_id)
                        if poids:
                            poids_attribute_id, poids_attribute_value_id = self.get_attributes('Poids', poids)
                            self.create_attribute_line(product_template_id, poids_attribute_id, poids_attribute_value_id)
                        if hauteur:
                            hauteur_attribute_id, hauteur_attribute_value_id = self.get_attributes('Hauteur', hauteur)
                            self.create_attribute_line(product_template_id, hauteur_attribute_id, hauteur_attribute_value_id)
                        if largeur:
                            largeur_attribute_id, largeur_attribute_value_id = self.get_attributes('Largeur', largeur)
                            self.create_attribute_line(product_template_id, largeur_attribute_id, largeur_attribute_value_id)
                        if epaisseur:
                            self.create_attribute_line(product_template_id, epaisseur_attribute_id, epaisseur_attribute_value_id)
                            epaisseur_attribute_id, epaisseur_attribute_value_id = self.get_attributes('Epaisseur', epaisseur)
                        if dent:
                            dent_attribute_id, dent_attribute_value_id = self.get_attributes('Nombre de dents', dent)
                            self.create_attribute_line(product_template_id, dent_attribute_id, dent_attribute_value_id)
                        if model:
                            model_attribute_id, model_attribute_value_id = self.get_attributes('Modèle', model)
                            self.create_attribute_line(product_template_id, model_attribute_id, model_attribute_value_id)
                        if direction:
                            direction_attribute_id, direction_attribute_value_id = self.get_attributes('Direction', direction)
                            self.create_attribute_line(product_template_id, direction_attribute_id, direction_attribute_value_id)
                        if materiel:
                            materiel_attribute_id, materiel_attribute_value_id = self.get_attributes('Matériel', materiel)
                            self.create_attribute_line(product_template_id, materiel_attribute_id, materiel_attribute_value_id)
                        if cote:
                            cote_attribute_id, cote_attribute_value_id = self.get_attributes('Côté', cote)
                            self.create_attribute_line(product_template_id, cote_attribute_id, cote_attribute_value_id)
                        if filetage:
                            filetage_attribute_id, filetage_attribute_value_id = self.get_attributes('Filetage', filetage)
                            self.create_attribute_line(product_template_id, filetage_attribute_id, filetage_attribute_value_id)
        return True

    def get_attributes(self, attribute_name, attribute_value):
        attribute_obj_search = self.env['product.attribute'].search([('name', '=', attribute_name)])
        if attribute_obj_search:
            attribute_id = attribute_obj_search
        else:
            attribute_id = self.env['product.attribute'].create({'name': attribute_name})

        attribute_value_obj_search = self.env['product.attribute.value'].search(
            [('name', '=', attribute_value), ('attribute_id', '=', attribute_id.id)])
        if attribute_value_obj_search:
            attribute_value_id = attribute_value_obj_search
        else:
            attribute_value_id = self.env['product.attribute.value'].create(
                {'name': attribute_value, 'attribute_id': attribute_id.id})
        return  attribute_id, attribute_value_id

    def return_value(self, template_id, attribute_name):
        value = ''
        attribute = self.env["product.attribute"].search([('name', '=', attribute_name)])
        if attribute:
            product_template_attribute_line_obj_search = self.env['product.template.attribute.line'].search([
                ('product_tmpl_id', '=', template_id),
                ('attribute_id', '=', attribute.id)
            ])
            value_ids = []
            for obj in product_template_attribute_line_obj_search:
                self._cr.execute(
                    "select product_attribute_value_id from product_attribute_value_product_template_attribute_line_rel"
                    " where product_template_attribute_line_id = {}".format(obj.id))
                for row in self._cr.fetchall():
                    value_ids.append((row[0]))
            product_value_obj_search = self.env['product.attribute.value'].search([('id', 'in', value_ids)])
            if product_value_obj_search:
                for obj in product_value_obj_search:
                    value += ',{}'.format(obj.name)
                value = value.split(',')[1]
        return value

    def export_sol(self):
        #directory = "/opt/bitnami/odoo/lib/odoo-15.0.post20211110-py3.8.egg/odoo/addons/web/static/reporting/"
        directory = "C://Users//Yassine//PycharmProjects//cicofap//Scripts//odoo//addons//web//static//reporting//"
        directory = "C://Program Files//Odoo15//server//odoo//addons//web//static//reporting//"
        fichier = "Articles_" + time.strftime("%H%M%S") + ".xlsx"
        workbook = xlsxwriter.Workbook(directory + fichier)
        style_title = workbook.add_format(
            {
                "bg_color": "#003366",
                "color": "white",
                "text_wrap": True,
                "bold": 1,
                "align": "center",
                "valign": "vcenter",
                "top": 1,
                "bottom": 1,
            }
        )
        style1 = workbook.add_format(
            {
                "text_wrap": True,
                "align": "center",
                "valign": "vcenter",
                "top": 1,
                "bottom": 1,
            }
        )

        feuille = workbook.add_worksheet("Articles")
        feuille.set_zoom(85)
        feuille.freeze_panes(1, 0)
        feuille.set_tab_color("yellow")
        feuille.set_column("A:L", 25)
        x = 1
        feuille.write("A" + str(x), "category", style_title)
        feuille.write("B" + str(x), "code", style_title)
        feuille.write("C" + str(x), "designation", style_title)
        feuille.write("D" + str(x), "marque", style_title)
        feuille.write("E" + str(x), "oem", style_title)
        feuille.write("F" + str(x), "cross", style_title)
        feuille.write("G" + str(x), "compatibilities", style_title)
        feuille.write("H" + str(x), "type", style_title)
        feuille.write("I" + str(x), "dimension", style_title)
        feuille.write("J" + str(x), "weight", style_title)
        feuille.write("K" + str(x), "height", style_title)
        feuille.write("L" + str(x), "width", style_title)
        feuille.write("M" + str(x), "thickness", style_title)
        feuille.write("N" + str(x), "dent", style_title)
        feuille.write("O" + str(x), "model", style_title)
        feuille.write("P" + str(x), "direction", style_title)
        feuille.write("Q" + str(x), "materiel", style_title)
        feuille.write("R" + str(x), "cote", style_title)
        feuille.write("S" + str(x), "filetage", style_title)
        feuille.write("T" + str(x), "cout", style_title)
        feuille.write("U" + str(x), "sale_price", style_title)
        feuille.write("V" + str(x), "tva", style_title)
        feuille.write("W" + str(x), "supplier", style_title)
        feuille.write("X" + str(x), "ref_supplier", style_title)
        feuille.write("Y" + str(x), "purchase_price", style_title)
        feuille.write("Z" + str(x), "devise_achat", style_title)

        records = self.env["product.template"].search([])
        x = x + 1
        for record in records:
            category = ''
            category_id = self.env["product.category"].search([('id', '=', record.categ_id.id)])
            if category_id:
                category = category_id.name
            marque = self.return_value(record.id, 'Marque de voiture')
            oem = self.return_value(record.id, 'OEM')
            cross = self.return_value(record.id, 'CROSS')
            dimension = self.return_value(record.id, 'Dimension')
            type = self.return_value(record.id, 'Type')
            weight = self.return_value(record.id, 'Poids')
            height = self.return_value(record.id, 'Hauteur')
            width = self.return_value(record.id, 'Largeur')
            thickness = self.return_value(record.id, 'Epaisseur')
            dent = self.return_value(record.id, 'Nombre de dents')
            model = self.return_value(record.id, 'Modèle')
            direction = self.return_value(record.id, 'Direction')
            materiel = self.return_value(record.id, 'Matériel')
            cote = self.return_value(record.id, 'Côté')
            filetage = self.return_value(record.id, 'Filetage')
            attribute = self.env["product.attribute"].search([('name', '=', 'Type')])
            supplier = ''
            purchase_price = ''
            reference = ''
            purchase_devise = ''
            product_supplier_obj_search = self.env['product.supplierinfo'].search([('product_tmpl_id', '=', record.id)], limit=1)
            if product_supplier_obj_search:
                supplier_id = product_supplier_obj_search.name
                if supplier_id:
                    supplier_obj_search = self.env['res.partner'].search([('id', '=', supplier_id.id)])
                    if supplier_obj_search:
                        supplier = supplier_obj_search.name
                if product_supplier_obj_search.product_code:
                    reference = product_supplier_obj_search.product_code
                purchase_price = product_supplier_obj_search.price
                currency_id = product_supplier_obj_search.currency_id
                if currency_id:
                    currency_obj_search = self.env['res.currency'].search([('id', '=', currency_id.id)])
                    if currency_obj_search:
                        purchase_devise = currency_obj_search.name
            compatibilites = []
            compatibilities_obj_search = self.env['product.template.compatibility'].search([('template_id', '=', record.id)])
            if compatibilities_obj_search:
                for compatibility in compatibilities_obj_search:
                    compatibilites.append(compatibility.name)
            compatibilites = '\n'.join(compatibilites)
            feuille.write("A" + str(x), category, style1)
            feuille.write("B" + str(x), record.default_code, style1)
            feuille.write("C" + str(x), record.name, style1)
            feuille.write("D" + str(x), marque, style1)
            feuille.write("E" + str(x), oem, style1)
            feuille.write("F" + str(x), cross, style1)
            feuille.write("G" + str(x), compatibilites, style1)
            feuille.write("H" + str(x), type, style1)
            feuille.write("I" + str(x), dimension, style1)
            feuille.write("J" + str(x), weight, style1)
            feuille.write("K" + str(x), height, style1)
            feuille.write("L" + str(x), width, style1)
            feuille.write("M" + str(x), thickness, style1)
            feuille.write("N" + str(x), dent, style1)
            feuille.write("O" + str(x), model, style1)
            feuille.write("P" + str(x), direction, style1)
            feuille.write("Q" + str(x), materiel, style1)
            feuille.write("R" + str(x), cote, style1)
            feuille.write("S" + str(x), filetage, style1)
            feuille.write("T" + str(x), record.standard_price, style1)
            feuille.write("U" + str(x), record.list_price, style1)
            feuille.write("V" + str(x), 0, style1)
            feuille.write("W" + str(x), supplier, style1)
            feuille.write("X" + str(x), reference, style1)
            feuille.write("Y" + str(x), purchase_price, style1)
            feuille.write("Z" + str(x), purchase_devise, style1)
            x = x + 1

        workbook.close()
        return self.get_return(fichier)

    def get_return(self, fichier):
        url = "/web/static/reporting/" + fichier
        if url:
            return {
                "type": "ir.actions.act_url",
                "target": "new",
                "url": url,
                "nodestroy": True,
            }
        else:
            return True

    def search_products(self):
        ids = []
        self._cr.execute("""select distinct(pt.id) from product_template_attribute_line ptal
                            inner join product_template pt on pt.id=ptal.product_tmpl_id
                            inner join(select id from product_attribute where name like 'OEM' or name like 'CROSS') as pa on pa.id=ptal.attribute_id
                            inner join product_attribute_value pav  on pa.id=pav.attribute_id
                            where pav.id||'_'||ptal.id in(select product_attribute_value_id||'_'||product_template_attribute_line_id
                            from product_attribute_value_product_template_attribute_line_rel)
                            and  (pt.default_code like '%%'||'{}'||'%%'
                            or pav.name like '%%'||'{}'||'%%') 
                            """.format(self.search_value, self.search_value))
        for res in self._cr.fetchall():
            ids.append(res[0])

        return {
            'name': _("Articles"),
            'type': 'ir.actions.act_window',
            'res_model': 'product.template',
            'view_mode': 'tree,form',
            'view_type': 'form',
            'views': [[False, 'tree'], [False, 'form'], ],
            'context': {},
            'domain': [('id', 'in', ids)],
            'target': 'current',

        }
class ProductImportImages(models.Model):
    _name = 'product.import.image'

    file = fields.Binary(string="Fichier")
    file_name = fields.Char(string="Nom du fichier")
    option = fields.Selection([('xls', 'XLS')], default='xls')

    def isfloat(self, num):
        try:
            float(num)
            return True
        except ValueError:
            return False

    def import_file(self):
        """ function to import product details from csv and xlsx file """
        """ function to import product details from csv and xlsx file """
        # directory = "/opt/bitnami/odoo/lib/odoo-15.0.post20211110-py3.8.egg/odoo/addons/web/static/reporting/"
        # directory = "C://Users//Yassine//PycharmProjects//cicofap//Scripts//odoo//addons//web//static//reporting//"
        directory = "C://Program Files//Odoo15//server//odoo//addons//web//static//reporting//"
        fichier = "Articles_" + time.strftime("%H%M%S") + ".xlsx"
        workbook = xlsxwriter.Workbook(directory + fichier)
        style_title = workbook.add_format(
            {
                "bg_color": "#003366",
                "color": "white",
                "text_wrap": True,
                "bold": 1,
                "align": "center",
                "valign": "vcenter",
                "top": 1,
                "bottom": 1,
            }
        )
        style1 = workbook.add_format(
            {
                "text_wrap": True,
                "align": "center",
                "valign": "vcenter",
                "top": 1,
                "bottom": 1,
            }
        )

        feuille = workbook.add_worksheet("Articles")
        feuille.freeze_panes(1, 0)
        feuille.set_tab_color("yellow")
        feuille.set_column("A:A", 25)
        feuille.set_column("B:B", 60)
        x = 1
        feuille.write("A" + str(x), "Référence Interne", style_title)
        feuille.write("B" + str(x), "Lien", style_title)
        x += 1
        if self.option == 'csv':
            try:
                file = base64.b64decode(self.file)
                file_string = file.decode('utf-8')
                file_string = file_string.split('\n')
            except Exception as e:
                raise Warning(_("Please choose the correct file! {}".format(e)))

            firstline = True
            for file_item in file_string:
                if firstline:
                    firstline = False
                    continue
                product_temp = self.env['product.template'].search([('default_code', '=', file_item.split(",")[0])], limit=1)
                if not product_temp:
                    product_info = self.env['product.supplierinfo'].search([('product_code', '=', file_item.split(",")[0])], limit=1)
                    if product_info:
                        if product_info.product_tmpl_id.id:
                            product_temp = self.env['product.template'].search(
                                [('id', '=', product_info.product_tmpl_id.id)], limit=1)
                if product_temp.id:
                    if file_item.split(",")[0]:
                        if "http://" in file_item.split(",")[1] or "https://" in file_item.split(",")[1]:
                            link = file_item.split(",")[1]
                            image_response = requests.get(link)
                            image_thumbnail = base64.b64encode(image_response.content)
                            product_name = {
                                'default_code': file_item.split(",")[0],
                                'image_1920': image_thumbnail,
                            }
                            product_line = product_temp.write(product_name)
                        elif '//' in file_item.split(",")[1]:
                            with open(file_item.split(",")[1].strip(), 'rb') as file:
                                data = base64.b64encode(file.read())
                                product_name = {
                                    'default_code': file_item.split(",")[0],
                                    'image_1920': data,
                                }
                                product_temp = product_temp.write(product_name)
        if self.option == 'xls':
            try:
                file_string = tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx")
                file_string.write(binascii.a2b_base64(self.file))
                file_string.seek(0)
                values = {}
                book = xlrd.open_workbook(file_string.name)
                sheet = book.sheet_by_index(0)
            except Exception as e:
                raise Warning(_("Please choose the correct file! {}".format(e)))

            startline = True
            for i in range(sheet.nrows):
                if startline:
                    startline = False
                else:
                    line = list(sheet.row_values(i))
                    code = line[0]
                    link = line[1]
                    if self.isfloat(code) and not isinstance(code, str):
                        if float(code) == int(float(code)):
                            code = str(int(float(code)))
                    product_temp = self.env['product.template'].search([('default_code', '=', code)], limit=1)
                    if not product_temp:
                        product_info = self.env['product.supplierinfo'].search([('product_code', '=', code)], limit=1)
                        if product_info:
                            if product_info.product_tmpl_id.id:
                                product_temp = self.env['product.template'].search(
                                    [('id', '=', product_info.product_tmpl_id.id)], limit=1)
                    if product_temp:
                        if code:
                            if "http://" in link or "https://" in link:
                                image_response = requests.get(link)
                                image_thumbnail = base64.b64encode(image_response.content)
                                product_name = {
                                    'default_code': code,
                                    'image_1920': image_thumbnail,
                                }
                                product_line = product_temp.write(product_name)
                            elif 'D://' in link:
                                if exists(link):
                                    _logger.info('{} exist'.format(code))
                                    with open(link, 'rb') as file:
                                        data = base64.b64encode(file.read())
                                        product_name = {
                                            'default_code': code,
                                            'image_1920': data,
                                        }
                                        product_line = product_temp.write(product_name)
                                else:
                                    feuille.write("A" + str(x), code, style1)
                                    feuille.write("B" + str(x), link, style1)
                                    x += 1
                                    _logger.info('{} dosent exist'.format(code))
                    else:
                        feuille.write("A" + str(x), code, style1)
                        feuille.write("B" + str(x), link, style1)
                        x += 1

        workbook.close()
        return self.get_return(fichier)

    def get_return(self, fichier):
        url = "/web/static/reporting/" + fichier
        if url:
            return {
                "type": "ir.actions.act_url",
                "target": "new",
                "url": url,
                "nodestroy": True,
            }
        else:
            return True
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
