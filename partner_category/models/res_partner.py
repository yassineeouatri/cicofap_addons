# -*- coding: utf-8 -*-
from odoo import api, fields, models , _
from odoo.exceptions import ValidationError


class Partner(models.Model):
    _inherit = 'res.partner'


    category = fields.Selection([('radiateur', 'Radiateur'), ('siege', 'Siège')], 'Catégorie', default='radiateur')

    @api.model
    def _name_search(self, name, args=None, operator='ilike', limit=100, name_get_uid=None):
        args = args or []
        if name:
            args = ['|', '|', ('name', operator, name), ('category', operator, name), ('ref', operator, name)] + args
        return self._search(args, limit=limit, access_rights_uid=name_get_uid)