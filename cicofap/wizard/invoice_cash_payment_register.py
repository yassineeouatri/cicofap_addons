# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import time

from odoo import api, fields, models, _
from odoo.exceptions import UserError


class InvoiceCashPaymentRegister(models.TransientModel):
    _name = "invoice.cash.payment.register"
    _description = "Invoice Cash Payment Register"

    currency_id = fields.Many2one('res.currency', string="Devise", store=True, readonly=True)
    amount = fields.Monetary('Montant', currency_field='currency_id')
    payment_method = fields.Selection(
        [('virement', 'Virement'), ('cheque', 'Chèque'), ('cash', 'Espèce'), ('traite', 'Traite')],
        'Mode de paiement')
    no_payment = fields.Char('N° de Paiement')
    payment_file = fields.Binary(string="Fichier")
    payment_filename = fields.Char("Nom du fichier")

    @api.model
    def default_get(self, fields):
        res = super(InvoiceCashPaymentRegister, self).default_get(fields)
        # Get the information from the original model
        active_id = self.env.context.get('active_id')
        if active_id:
            original_record = self.env['invoice.cash'].browse(active_id)
            res.update({
                'amount': original_record.price_due
            })
        return res

    def create_payment(self):
        invoice_cash = self.env['invoice.cash'].browse(self._context.get('active_ids', []))
        cash_id = self.env['invoice.cash.payment'].create({
            'cash_id': invoice_cash.id,
            'currency_id': self.currency_id.id,
            'amount': self.amount,
            'payment_method': self.payment_method,
            'no_payment': self.no_payment,
            'payment_file': self.payment_file,
            'payment_filename': self.payment_filename
        })
        return {'type': 'ir.actions.act_window_close'}


