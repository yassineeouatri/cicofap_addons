# -*- coding: utf-8 -*-
from odoo import api, fields, models , _
from odoo.exceptions import ValidationError


class product_commercial(models.Model):
    _inherit = 'product.commercial'

    user_id = fields.Many2one('res.users', 'Utilisateur')

    def action_user_create_from_commercial(self):
        view = self.env.ref('commercial_user.view_commercial_user_form')
        return {
            'name': _('Créer un utilisateur'),
            'type': 'ir.actions.act_window',
            'res_model': 'product.commercial.user',
            'views': [(view.id, 'form')],
            'target': 'new',
            'context': {
                'default_commercial_id': self.id},
        }

    def action_user_delete_from_commercial(self):
        view = self.env.ref('commercial_user.view_delete_commercial_user_form')
        return {
            'name': _('Supprimer un utilisateur'),
            'type': 'ir.actions.act_window',
            'res_model': 'product.commercial.user',
            'views': [(view.id, 'form')],
            'target': 'new',
            'context': {
                'default_commercial_id': self.id},
        }