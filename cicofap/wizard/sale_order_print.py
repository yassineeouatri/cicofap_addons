# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models
import logging

_logger = logging.getLogger(__name__)

class SaleOrderPrint(models.TransientModel):
    _name = 'sale.order.print'
    _description = "Sales Order Print"

    partner_id = fields.Many2one('res.partner', 'Client', required=True)
    date_from = fields.Date('Date début', required=True)
    date_to = fields.Date('Date fin', required=True)
    warehouse_id = fields.Many2one('stock.warehouse', 'Entrepôt')
    type = fields.Selection([('invoice', 'Facture'), ('cash', 'Cash')], 'Type', required=True)

    def action_print(self):
        data = {
            'date_from': self.date_from,
            'date_to': self.date_to,
            'partner_id': self.partner_id.id,
            'warehouse_id': self.warehouse_id.id,
            'type': self.type
        }
        # docids = self.env['purchase.order'].search([]).ids
        return self.env.ref('cicofap.action_report_sale_order_print').report_action(1, data=data)
