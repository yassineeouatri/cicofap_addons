# -*- coding: utf-8 -*-
# Author: ALFAWEB

from odoo import _, api, fields, models, SUPERUSER_ID
from odoo.exceptions import UserError, AccessError
from odoo.exceptions import ValidationError


class ResPartner(models.Model):
    _name = 'res.partner'
    _inherit = 'res.partner'

    customer = fields.Boolean(string='Client',
                              help="Cochez cette case si ce contact est un client.")
    supplier = fields.Boolean(string='Fournisseur',
                              help="Cochez cette case si ce contact est un fournisseur.")