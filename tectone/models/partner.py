# -*- coding: utf-8 -*-
# Author: ALFAWEB

from odoo import _, api, fields, models, SUPERUSER_ID
from odoo.exceptions import UserError, AccessError
from odoo.exceptions import ValidationError


class ResPartner(models.Model):
    _name = 'res.partner'
    _inherit = 'res.partner'

    def _get_default_customer(self):
        return True

    customer = fields.Boolean(string='Client',
                              help="Cochez cette case si ce contact est un client.", default=_get_default_customer)
    supplier = fields.Boolean(string='Fournisseur',
                              help="Cochez cette case si ce contact est un fournisseur."
                                   "S'il n'est pas coché, les fournisseurs ne le verront pas lors de l'encodage d'un bon de commande.")