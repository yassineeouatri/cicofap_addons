# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models
import logging

_logger = logging.getLogger(__name__)

class PartnerMErge(models.TransientModel):
    _name = 'res.partner.merge'
    _description = "Fusionner 2 clients"

    dest_partner_id = fields.Many2one('res.partner', 'Client à garder', required=True)
    src_partner_id = fields.Many2one('res.partner', 'Client à archiver', required=True)

    def action_merge(self):
        self._cr.execute("update sale_order set partner_id={} where partner_id={}".format(self.dest_partner_id.id,
                                                                                          self.src_partner_id.id))
        self._cr.execute("update account_move set partner_id={} where partner_id={}".format(self.dest_partner_id.id,
                                                                                          self.src_partner_id.id))
        self._cr.execute("update purchase_order set partner_id={} where partner_id={}".format(self.dest_partner_id.id,
                                                                                            self.src_partner_id.id))
        self._cr.execute("update account_payment set partner_id={} where partner_id={}".format(self.dest_partner_id.id,
                                                                                              self.src_partner_id.id))
        self._cr.execute("update stock_picking set partner_id={} where partner_id={}".format(self.dest_partner_id.id,
                                                                                               self.src_partner_id.id))
        self._cr.execute("update res_partner set active='f' where id={}".format(self.src_partner_id.id))
        return True
