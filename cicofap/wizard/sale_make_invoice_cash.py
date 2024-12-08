# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import time

from odoo import api, fields, models, _
from odoo.exceptions import UserError

class SaleMakePayment(models.TransientModel):
    _name = "sale.make.payment"
    _description = "Sales Make Payment"

class SaleMakeInvoiceCash(models.TransientModel):
    _name = "sale.make.invoice.cash"
    _description = "Sales Make Invoice Cash"

    advance_payment_method = fields.Selection([('delivered', 'Cash'),], string='Créer un cash', default='delivered', required=True)

    def create_invoices(self):
        sale_order = self.env['sale.order'].browse(self._context.get('active_ids', []))
        cash_id = self.env['invoice.cash'].create({
            'order_id': sale_order.id,
            'partner_id': sale_order.partner_id.id
        })
        tax_id = self.env['account.tax'].search([('type_tax_use', '=', 'sale'), ('amount', '=', '20')]).id
        for line in sale_order.order_line:
            cash_line = {
                'line_id': cash_id.id,
                'quantity': line.qty_delivered,
                'discount': line.discount,
                'price_unit': line.price_unit,
                'partner_id': sale_order.partner_id.id,
                'product_id': line.product_id.id,
                'tax_id': tax_id
            }
            self.env['invoice.cash.line'].create(cash_line)
        if self._context.get('open_invoices', False):
            return self.action_view_cash(cash_id.id)
        return {'type': 'ir.actions.act_window_close'}

    def action_view_cash(self, cash_id):
        self.ensure_one()
        result = {
            "type": "ir.actions.act_window",
            "res_model": "invoice.cash",
            "domain": [('id', 'in', [cash_id])],
            "context": {"create": False},
            "name": "Cash",
            'view_mode': 'tree,form',
        }
        return result

