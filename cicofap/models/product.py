# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import itertools
import logging
from collections import defaultdict

from odoo import api, fields, models, tools, _, SUPERUSER_ID
from odoo.exceptions import ValidationError, RedirectWarning, UserError
from odoo.osv import expression

_logger = logging.getLogger(__name__)

class product_template(models.Model):
    _inherit = 'product.template'

    detailed_type = fields.Selection(default='product')
    supplier_id = fields.Many2one('res.partner', 'Fournisseur')
    marque_id = fields.Many2one('product.marque', 'Marque')
    weight = fields.Float('Poids')
    height = fields.Float('Hauteur')
    width = fields.Float('Largeur')
    epaisseur = fields.Float('Epaisseur')
    dents = fields.Integer('Nombre de dents')
    availability = fields.Char(store=True, readonly=False, compute='_compute_availability', string="Disponibilité")
    compatibility_ids = fields.One2many('product.template.compatibility', 'template_id', 'Compatibilité')
    categ_type = fields.Selection([('siege', 'SIEGE'), ('radiateur', 'RADIATEUR')], compute='_compute_categ_type', string="Catégorie", store=True)
    compatibility_count = fields.Integer(compute='_product_template_compatibility_count', string='# Compatibilities')

    @api.depends('compatibility_ids')
    def _product_template_compatibility_count(self):
        for rec in self:
            rec.compatibility_count = len(rec.compatibility_ids)

    def action_view_compatibility(self):
        self.ensure_one()
        action = self.env["ir.actions.actions"]._for_xml_id("cicofap.action_product_template_compatibility")
        action['domain'] = [('template_id', '=', self.id)]
        return action

    @api.depends('qty_available')
    def _compute_availability(self):
        ''' Load initial values from the account.moves passed through the context. '''
        for wizard in self:
            if wizard.qty_available > 0:
                wizard.availability = 'En stock'
            else:
                wizard.availability = 'En rupture'

    @api.depends('categ_id')
    def _compute_categ_type(self):
        ''' Load initial values from the account.moves passed through the context. '''
        for record in self:
            if 'RADIATEUR' in record.categ_id.display_name:
                record.categ_type = 'radiateur'
            else:
                record.categ_type = 'siege'

    def name_get(self):
        res = super(product_template, self).name_get()
        self.browse(self.ids).read(['default_code'])
        return [(template.id, '%s' % template.default_code or '') for template in self]

    def action_view_product_movement(self):
        self.ensure_one()
        action = self.env["ir.actions.actions"]._for_xml_id("cicofap.product_movement_report_action")
        action['domain'] = [('product_id.product_tmpl_id', 'in', self.ids)]
        return action

    def action_product_template_add(self):
        partner_id = self.env['res.users'].search([('id', '=', self.env.user.id)]).partner_id.id
        if not partner_id:
            raise UserError(_('Chaque utilisateur doit être lié à un client. Merci de contacter votre administrateur'))
        else:
            product_template_id = self.id
            products = self.env['product.product'].search([('product_tmpl_id', '=', product_template_id)])
            product_id = products[0].id
            orders = self.env['sale.order'].search([('state', '=', 'new'),('partner_id', '=', partner_id)])

            view = self.env.ref('sh_message.sh_message_wizard')
            view_id = view or view.id or False
            context = dict(self._context or {})
            if len(orders) == 0:
                order = self.env['sale.order'].create({
                    'partner_id': partner_id,
                    'state': 'new'
                })
                print(1)
                vals = [{'sequence': 10, 'display_type': False, 'product_id': product_id,
                         'product_template_id': product_template_id, 'name': self.name, 'product_uom_qty': 1,
                         'product_uom': 1, 'product_packaging_qty': 0, 'product_packaging_id': False, 'discount': 0,
                         'order_id': order.id}]
                self.env['sale.order.line'].create(vals)
                context['message'] = "Une nouvelle commande à l'état brouillon a été crée. Le produit a été bien ajouté à la commande"
                return  {
                    'name': 'Succès',
                    'type': 'ir.actions.act_window',
                    'view_mode': 'form',
                    'view_type': 'form',
                    'res_model': 'sh.message.wizard',
                    'views':[(view.id, 'form')],
                    'view_id': view.id,
                    'target':'new',
                    'context': context

                }
            elif len(orders) == 1:
                order_id = orders[0].id
                order_lines = self.env['sale.order.line'].search([('product_template_id', '=', product_template_id), ('order_id', '=', order_id)])
                if len(order_lines) == 0:
                    vals = [{'sequence': 10, 'display_type': False, 'product_id': product_id, 'product_template_id': product_template_id, 'name': self.name, 'product_uom_qty': 1, 'product_uom': 1, 'product_packaging_qty': 0, 'product_packaging_id': False, 'discount': 0, 'order_id': order_id}]
                    self.env['sale.order.line'].create(vals)
                    context['message'] = "Le produit a été bien ajouté à la commande"
                    return {
                        'name': 'Succès',
                        'type': 'ir.actions.act_window',
                        'view_mode': 'form',
                        'view_type': 'form',
                        'res_model': 'sh.message.wizard',
                        'views': [(view.id, 'form')],
                        'view_id': view.id,
                        'target': 'new',
                        'context': context

                    }
                else:
                    raise UserError(_('Ce produit a été déjà ajouté à la commande'))
            else:
                raise UserError(_("Vous devez avoir une seule commande à l'état brouillon afin d'ajouter ce produit"))

        return True

class product_product(models.Model):
    _inherit = 'product.product'

    def name_get(self):
        res = super(product_product, self).name_get()

        def _name_get(d):
            code = self._context.get('display_default_code', True) and d.get('default_code', False) or False
            if code:
                name = '%s' % (code)
            else :
                name = d.get('name', '')
            return (d['id'], name)

        partner_id = self._context.get('partner_id')
        if partner_id:
            partner_ids = [partner_id, self.env['res.partner'].browse(partner_id).commercial_partner_id.id]
        else:
            partner_ids = []
        company_id = self.env.context.get('company_id')

        # all user don't have access to seller and partner
        # check access and use superuser
        self.check_access_rights("read")
        self.check_access_rule("read")

        result = []

        # Prefetch the fields used by the `name_get`, so `browse` doesn't fetch other fields
        # Use `load=False` to not call `name_get` for the `product_tmpl_id`
        self.sudo().read(['name', 'default_code', 'product_tmpl_id'], load=False)

        product_template_ids = self.sudo().mapped('product_tmpl_id').ids

        if partner_ids:
            supplier_info = self.env['product.supplierinfo'].sudo().search([
                ('product_tmpl_id', 'in', product_template_ids),
                ('name', 'in', partner_ids),
            ])
            # Prefetch the fields used by the `name_get`, so `browse` doesn't fetch other fields
            # Use `load=False` to not call `name_get` for the `product_tmpl_id` and `product_id`
            supplier_info.sudo().read(['product_tmpl_id', 'product_id', 'product_name', 'product_code'], load=False)
            supplier_info_by_template = {}
            for r in supplier_info:
                supplier_info_by_template.setdefault(r.product_tmpl_id, []).append(r)
        for product in self.sudo():
            variant = product.product_template_attribute_value_ids._get_combination_name()

            name = variant and "%s (%s)" % (product.name, variant) or product.name
            sellers = self.env['product.supplierinfo'].sudo().browse(self.env.context.get('seller_id')) or []
            if not sellers and partner_ids:
                product_supplier_info = supplier_info_by_template.get(product.product_tmpl_id, [])
                sellers = [x for x in product_supplier_info if x.product_id and x.product_id == product]
                if not sellers:
                    sellers = [x for x in product_supplier_info if not x.product_id]
                # Filter out sellers based on the company. This is done afterwards for a better
                # code readability. At this point, only a few sellers should remain, so it should
                # not be a performance issue.
                if company_id:
                    sellers = [x for x in sellers if x.company_id.id in [company_id, False]]
            if sellers:
                for s in sellers:
                    seller_variant = s.product_name and (
                            variant and "%s (%s)" % (s.product_name, variant) or s.product_name
                    ) or False
                    mydict = {
                        'id': product.id,
                        'name': seller_variant or name,
                        'default_code': s.product_code or product.default_code,
                    }
                    temp = _name_get(mydict)
                    if temp not in result:
                        result.append(temp)
            else:
                mydict = {
                    'id': product.id,
                    'name': name,
                    'default_code': product.default_code,
                }
                result.append(_name_get(mydict))
        return result

    def get_product_multiline_description_sale(self):
        """ Compute a multiline description of this product, in the context of sales
                (do not use for purchases or other display reasons that don't intend to use "description_sale").
            It will often be used as the default description of a sale order line referencing this product.
        """
        res = super(product_product, self).get_product_multiline_description_sale()
        name = self.name
        if self.description_sale:
            name += '\n' + self.description_sale

        return name

    def action_view_product_movement(self):
        self.ensure_one()
        action = self.env["ir.actions.actions"]._for_xml_id("cicofap.product_movement_report_action")
        action['domain'] = [('product_id', '=', self.id)]
        return action

    def action_view_compatibility(self):
        self.ensure_one()
        action = self.env["ir.actions.actions"]._for_xml_id("cicofap.action_product_template_compatibility")
        action['domain'] = [('template_id', '=', self.id)]
        return action

class product_marque(models.Model):
    _name = 'product.marque'
    _description = "Marques des voitures"
    _order = "name"

    name = fields.Char('Marque')
    parent_id = fields.Many2one('product.marque', 'Marque mère')

class product_manufacturer(models.Model):
    _name = 'product.manufacturer'
    _description = "Fabriquants"
    _order = "name"

    name = fields.Char('Fabriquant')

class product_manufacturer_model(models.Model):
    _name = 'product.manufacturer.model'
    _description = "Models"
    _order = "name"

    name = fields.Char('Modèle')

class product_manufacturer_serie(models.Model):
    _name = 'product.manufacturer.serie'
    _description = "Séries"
    _order = "name"

    name = fields.Char('Modèle Série')

class product_engine_type(models.Model):
    _name = 'product.engine.type'
    _description = "Types Engines"
    _order = "name"

    name = fields.Char('Type engine')

class product_motor_type(models.Model):
    _name = 'product.motor.type'
    _description = "Types moteurs"
    _order = "name"

    name = fields.Char('Type moteur')

class product_drive_type(models.Model):
    _name = 'product.drive.type'
    _description = "Types de tractions"
    _order = "name"

    name = fields.Char('Type traction')

class product_body_type(models.Model):
    _name = 'product.body.type'
    _description = "Types de corps"
    _order = "name"

    name = fields.Char('Type corps')

class product_template_compatibility(models.Model):
    _name = 'product.template.compatibility'
    _description = "Compatibility"
    _order="name"

    name = fields.Char('Compatibilité')
    manufacturer_id = fields.Many2one('product.manufacturer', 'Fabriquant')
    model_id = fields.Many2one('product.manufacturer.model', 'Modèle')
    serie_id = fields.Many2one('product.manufacturer.serie', 'Modèle série')
    motor_type_id = fields.Many2one('product.motor.type', 'Motor Type')
    displacement = fields.Char('Displacement')
    model_year_from = fields.Char('Model Year From')
    model_year_to = fields.Char('Model Year To')
    model_year = fields.Char('Années Modèle')
    body_type_id = fields.Many2one('product.body.type', 'Body Type')
    drive_type_id = fields.Many2one('product.drive.type', 'Drive Type')
    engine_type_id = fields.Many2one('product.engine.type', 'Engine Type')
    engine_code = fields.Char('Engine Code')
    type = fields.Char('Type')
    kw = fields.Integer('kw')
    hp = fields.Integer('hp')
    cylinder = fields.Integer('Cylindre')
    valve = fields.Integer('valve')
    template_id = fields.Many2one('product.template', 'Article')
    # to delete
    motor_type = fields.Char('')
    body_type = fields.Char('')
    drive_type = fields.Char('')
    engine_type = fields.Char('')


