# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class UserPartner(models.Model):
    _name = 'res.partner.user'

    partner_id = fields.Many2one('res.partner', 'Partenaire')
    login = fields.Char(string="Login",  help="Login")
    password = fields.Char(string="Mot de passe")

    def create_user(self):
        partner = self.env['res.partner'].search([('id', '=', self.partner_id.id)], limit=1)
        if not partner.email:
            partner.write({'email': ' '})
        group_id = self.env['res.groups'].search([('name', '=', 'Client')], limit=1).id
        user = self.env['res.users'].search([('partner_id', '=', self.partner_id.id)], limit=1)
        if user:
            user.write({'name': self.partner_id.name,
                          'partner_id': self.partner_id.id,
                          'login': self.login,
                          'password': self.password,
                          })
        else:
            user = self.env['res.users'].create({'name': self.partner_id.name,
                                          'partner_id': self.partner_id.id,
                                          'login': self.login,
                                          'password': self.password,
                                         })
        if user:
            self._cr.execute(f"DELETE FROM res_groups_users_rel WHERE uid={user.id}")
            self._cr.execute(f"DELETE FROM res_partner_users_sale_rel WHERE res_partner_id={self.partner_id.id}")
            self._cr.execute(f"INSERT INTO res_partner_users_sale_rel(res_partner_id, res_users_id) VALUES({self.partner_id.id},{user.id})")
            user.write({'groups_id': [(6, 0 , [group_id])]})
        return

    def delete_user(self):
        user = self.env['res.users'].search([('partner_id', '=', self.partner_id.id)], limit=1)
        if user:
            user.unlink()
        return