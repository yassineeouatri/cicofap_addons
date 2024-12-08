# -*- coding: utf-8 -*-
from odoo import api, fields, models , _
from odoo.exceptions import ValidationError


class Partner(models.Model):
    _inherit = 'res.partner'

    commercial_id = fields.Many2one('product.commercial', 'Commercial')


class Commercial(models.Model):
    _inherit = 'product.commercial'

    partner_ids = fields.One2many('res.partner', 'commercial_id', 'Partenaires')
    partner_count = fields.Integer(compute='_compute_partner_count', string='# Partenaires')

    @api.depends('partner_ids')
    def _compute_partner_count(self):
        for rec in self:
            rec.partner_count = len(rec.partner_ids)

    def action_view_partner(self):
        self.ensure_one()
        action = self.env["ir.actions.actions"]._for_xml_id("base.action_partner_form")
        action['domain'] = [('commercial_id', '=', self.id)]
        return action