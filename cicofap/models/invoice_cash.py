# -*- coding: utf-8 -*-

from odoo.models import NewId
from odoo import api, fields, models, Command, _
from odoo.exceptions import RedirectWarning, UserError, ValidationError, AccessError
from odoo.tools import float_compare, date_utils, email_split, email_re, html_escape, is_html_empty
from odoo.tools.misc import formatLang, format_date, get_lang

from datetime import date, timedelta
from collections import defaultdict
from contextlib import contextmanager
from itertools import zip_longest
from hashlib import sha256
from json import dumps

import ast
import json
import re
import warnings

PAYMENT_STATE_SELECTION = [
        ('not_paid', 'Non payée'),
        ('paid', 'Payée'),
        ('partial', 'Partiellement payée'),
]

class InvoiceCash(models.Model):
    _name = "invoice.cash"
    _description = "Invoice Cash"
    _order = 'date desc'

    @api.model
    def _get_default_currency(self):
        return self.env.company.currency_id

    # ==== Business fields ====
    name = fields.Char('Numéro', default=lambda self: _('New'))
    order_id = fields.Many2one('sale.order', 'Commande')
    date = fields.Date(string='Date', required=True, readonly=True, states={'draft': [('readonly', False)]}, default=fields.Date.context_today)
    ref = fields.Char(string='Reference')
    state = fields.Selection(selection=[('draft', 'Brouillon'), ('done', 'Validée'), ('cancel', 'Annulée')], string='Etat', required=True, readonly=True, default='draft')
    currency_id = fields.Many2one('res.currency', store=True, readonly=True, required=True, states={'draft': [('readonly', False)]}, string='Currency', default=_get_default_currency)
    line_ids = fields.One2many('invoice.cash.line', 'line_id', string='Lines', copy=True, readonly=True, states={'draft': [('readonly', False)]})
    payment_ids = fields.One2many('invoice.cash.payment', 'cash_id', string='Cashs', copy=True, readonly=True, states={'draft': [('readonly', False)]})
    partner_id = fields.Many2one('res.partner', readonly=True, tracking=True, states={'draft': [('readonly', False)]}, string='Client')
    payment_state = fields.Selection(PAYMENT_STATE_SELECTION, string="Etat du paiement", readonly=True, compute='_compute_amount')
    discount = fields.Float(string='Remise (%)', digits='Discount', default=0.0)
    # === Amount fields ===
    price_untaxed = fields.Monetary(string='Montant HT', readonly=True, currency_field='currency_id', compute='_compute_amount')
    price_tax = fields.Monetary(string='TVA', store=True, currency_field='currency_id', compute='_compute_amount')
    price_total = fields.Monetary(string='Montant TTC', readonly=True, currency_field='currency_id', compute='_compute_amount')
    price_payed = fields.Monetary(string='Montant Payé', readonly=True, currency_field='currency_id', compute='_compute_amount')
    price_due = fields.Monetary(string='Montant Restant', readonly=True, currency_field='currency_id', compute='_compute_amount')

    @api.model
    def create(self, vals):
        if vals.get('name', _('New')) == _('New'):
            vals['name'] = self.env['ir.sequence'].next_by_code('invoice.cash') or _('New')

        result = super(InvoiceCash, self).create(vals)
        return result

    def _compute_amount(self):
        for record in self:
            total = sum([line.price_total for line in record.line_ids])
            record.price_untaxed = sum([line.price_untaxed for line in record.line_ids])
            record.price_tax = sum([line.price_tax for line in record.line_ids])
            record.price_total = sum([line.price_total for line in record.line_ids])
            record.price_payed = sum([line.amount for line in record.payment_ids if line.state == 'posted'])
            record.price_due = sum([line.price_total for line in record.line_ids]) - sum([line.amount for line in record.payment_ids if line.state == 'posted'])

            if record.price_payed == 0:
                record.payment_state = 'not_paid'
            elif record.price_payed >= record.price_total:
                record.payment_state = 'paid'
            else:
                record.payment_state = 'partial'

    def button_draft(self):
        self.write({'state': 'draft'})

    def button_done(self):
        self.write({'state': 'done'})

    def button_cancel(self):
        self.write({'state': 'cancel'})

class InvoiceCashLine(models.Model):
    _name = "invoice.cash.line"
    _description = "Lignes de facture"
    _order = "date desc"

    @api.model
    def _get_default_currency(self):
        return self.env.company.currency_id

    # ==== Business fields ====
    line_id = fields.Many2one('invoice.cash', string='Journal Entry', index=True, required=True, readonly=True, auto_join=True, ondelete="cascade")
    date = fields.Date(related='line_id.date', store=True, readonly=True)
    ref = fields.Char(related='line_id.ref', store=True, copy=False, index=True, readonly=True)
    parent_state = fields.Selection(related='line_id.state', store=True, readonly=True)
    sequence = fields.Integer(default=10)
    name = fields.Char(string='Label', tracking=True)
    quantity = fields.Float(string='Quantité', default=1.0, digits='Product Unit of Measure')
    price_unit = fields.Float(string='Prix unitaire')
    tax_id = fields.Many2one('account.tax', 'TVA')
    discount = fields.Float(string='Remise (%)', digits='Discount', default=0.0)
    price_untaxed = fields.Monetary(string='Montant HT', store=True, readonly=True, currency_field='currency_id', compute='_compute_price_total')
    price_tax = fields.Monetary(string='Montant TVA', store=True, readonly=True, currency_field='currency_id', compute='_compute_price_total')
    price_total = fields.Monetary(string='Montant TTC', store=True, readonly=True, currency_field='currency_id', compute='_compute_price_total')
    currency_id = fields.Many2one('res.currency', string='Devise', default=_get_default_currency)
    partner_id = fields.Many2one('res.partner', string='Client', ondelete='restrict')
    product_id = fields.Many2one('product.product', string='Article', ondelete='restrict', required=True)
    name = fields.Char(related='product_id.name', string='Libellé', store=True, readonly=True)

    @api.depends('quantity', 'price_unit', 'tax_id', 'discount')
    def _compute_price_total(self):
        for record in self:
            price_untaxed = record.quantity * record.price_unit
            price_tax = 0
            price_discount = 0
            prince_total = 0
            if record.discount:
                price_untaxed = record.quantity * record.price_unit * (1 - round(record.discount * 1.00 / 100, 2))

            if record.tax_id:
                price_tax = price_untaxed * round(record.tax_id.amount * 1.00 / 100, 2)

            record.price_untaxed = price_untaxed
            record.price_tax = price_tax
            record.price_total = price_tax + price_untaxed

class InvoiceCashPayment(models.Model):
    _name = "invoice.cash.payment"
    _description = "Lignes de paiements"
    _order = "date desc"

    name = fields.Char('Numéro', default=lambda self: _('New'))
    cash_id = fields.Many2one('invoice.cash', string='Cash', index=True, required=True, readonly=True, auto_join=True, ondelete="cascade")
    date = fields.Date('Date de paiement', default=fields.Date.context_today)
    currency_id = fields.Many2one('res.currency', related='cash_id.currency_id', store=True, readonly=True)
    amount = fields.Monetary('Montant', currency_field='currency_id' )
    payment_method = fields.Selection(
        [('virement', 'Virement'), ('cheque', 'Chèque'), ('cash', 'Espèce'), ('traite', 'Traite')],
        'Mode de paiement')
    no_payment = fields.Char('N° Payment')
    payment_file = fields.Binary(string="Fichier")
    payment_filename = fields.Char("Nom du fichier")
    state = fields.Selection([('draft', 'Brouillon'), ('posted', 'Comptabilisé'), ('cancel', 'Annulé')], 'Etat', default='draft')

    @api.model
    def create(self, vals):
        if vals.get('name', _('New')) == _('New'):
            vals['name'] = self.env['ir.sequence'].next_by_code('invoice.cash.payment') or _('New')

        result = super(InvoiceCashPayment, self).create(vals)
        return result
    def action_post(self):
        self.write({'state': 'posted'})
        if self.name == _('New'):
            self.write({'name': self.env['ir.sequence'].next_by_code('invoice.cash.payment') or _('New')})

    def action_cancel(self):
        self.write({'state': 'cancel'})

    def action_draft(self):
        self.write({'state': 'draft'})