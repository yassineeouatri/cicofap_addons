# -*- coding: utf-8 -*-
from odoo import api, fields, models , _
from odoo.exceptions import ValidationError


class Partner(models.Model):
    _inherit = 'res.partner'


    def action_user_create_from_partner(self):
        view = self.env.ref('partner_user.view_partner_user_form')
        return {
            'name': _('Créer un utilisateur'),
            'type': 'ir.actions.act_window',
            'res_model': 'res.partner.user',
            'views': [(view.id, 'form')],
            'target': 'new',
            'context': {
                'default_partner_id': self.id},
        }

    def action_user_delete_from_partner(self):
        view = self.env.ref('partner_user.view_delete_partner_user_form')
        return {
            'name': _('Supprimer un utilisateur'),
            'type': 'ir.actions.act_window',
            'res_model': 'res.partner.user',
            'views': [(view.id, 'form')],
            'target': 'new',
            'context': {
                'default_partner_id': self.id},
        }