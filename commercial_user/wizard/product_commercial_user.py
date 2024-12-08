# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class ProductCommercialUser(models.Model):
    _name = 'product.commercial.user'

    commercial_id = fields.Many2one('product.commercial', 'Commercial')
    login = fields.Char(string="Login",  help="Login")
    password = fields.Char(string="Mot de passe")

    def create_user(self):
        commercial = self.env['product.commercial'].search([('id', '=', self.commercial_id.id)], limit=1)
        if not commercial.email:
            commercial.write({'email': ' '})
        group_id = self.env['res.groups'].search([('name', '=', 'Commercial')], limit=1).id
        user = commercial.user_id
        if user:
            user.write({'name': self.commercial_id.name,
                          'login': self.login,
                          'password': self.password,
                          })
        else:
            user = self.env['res.users'].create({'name': self.commercial_id.name,
                                          'login': self.login,
                                          'password': self.password,
                                         })
            commercial.write({'user_id': user.id})
        if user:
            self._cr.execute(f"DELETE FROM res_groups_users_rel WHERE uid={user.id}")
            user.write({'groups_id': [(6, 0 , [group_id])]})
        return

    def delete_user(self):
        commercial = self.env['product.commercial'].search([('id', '=', self.commercial_id.id)], limit=1)
        user = commercial.user_id
        if user:
            user.unlink()
        return