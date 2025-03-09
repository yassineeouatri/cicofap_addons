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
    type = fields.Selection([('cash', 'Cash'), ('credit', 'Avoir')], default='cash', string='Type')
    order_id = fields.Many2one('sale.order', 'Commande', readonly=True)
    parent_id = fields.Many2one('invoice.cash', 'Cash parent', readonly=True)
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
    price_text = fields.Text(compute="_compute_price_text", string="Montant en texte", readonly=True, store=True)

    def _get_report_base_filename(self):
        self.ensure_one()
        return 'Cash - %s' % (self.name)

    @api.model
    def create(self, vals):
        if vals.get('name', _('New')) == _('New'):
            vals['name'] = self.env['ir.sequence'].next_by_code('invoice.cash') or _('New')

        result = super(InvoiceCash, self).create(vals)
        return result

    @api.depends('price_total', 'currency_id')
    def _compute_price_text(self):
        for record in self:
            record.price_text = self.trad(record.price_total, record.currency_id.currency_unit_label,
                                            record.currency_id.currency_subunit_label)

    @api.depends('line_ids', 'payment_ids', 'type')
    def _compute_amount(self):
        for record in self:
            coeficient = 1 if record.type == 'cash' else -1
            total = sum([line.price_total for line in record.line_ids])
            record.price_untaxed = coeficient * sum([line.price_untaxed for line in record.line_ids])
            record.price_tax = coeficient * sum([line.price_tax for line in record.line_ids])
            record.price_total = coeficient * sum([line.price_total for line in record.line_ids])
            record.price_payed = sum([line.amount for line in record.payment_ids if line.state == 'posted'])
            record.price_due = coeficient * sum([line.price_total for line in record.line_ids]) - sum([line.amount for line in record.payment_ids if line.state == 'posted'])

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

    def create_credit(self):
        # On vérifie que l'objet 'cash' est dans l'état 'done' avant de créer un avoir
        if self.state != 'done':
            raise UserError("Le cash doit être validé avant de pouvoir créer un avoir.")

        # On crée un avoir (type='credit') en dupliquant les informations de la facture
        credit_vals = {
            'name': _('Avoir pour %s' % self.name),  # Nouveau nom pour l'avoir
            'type': 'credit',  # Type "Avoir"
            'order_id': self.order_id.id,  # La même commande
            'parent_id': self.id,  # L'avoir fait référence au cash original
            'date': fields.Date.context_today(self),  # Date actuelle
            'ref': self.ref,  # La même référence
            'partner_id': self.partner_id.id,  # Même client
            'currency_id': self.currency_id.id,  # Même devise
            'discount': self.discount,  # Remise (si applicable)
            'line_ids': [(0, 0, {
                'product_id': line.product_id.id,  # Duplique les lignes de la facture
                'quantity': line.quantity,
                'price_unit': line.price_unit,
                'discount': line.discount,
                'tax_id': line.tax_id.id,
                'price_untaxed': -line.price_untaxed,  # Montant HT négatif pour l'avoir
                'price_tax': -line.price_tax,  # Montant TVA négatif pour l'avoir
                'price_total': -line.price_total,  # Montant TTC négatif pour l'avoir
            }) for line in self.line_ids],
        }

        # Création de l'avoir
        credit_cash = self.env['invoice.cash'].create(credit_vals)

        return credit_cash

    def tradd(self, num):
        global t1, t2
        ch = ""
        if num == 0:
            ch = ""
        elif num < 20:
            ch = t1[num]
        elif num >= 20:
            if (num >= 70 and num <= 79) or (num >= 90):
                z = int(num / 10) - 1
            else:
                z = int(num / 10)
            ch = t2[z]
            num = num - z * 10
            if (num == 1 or num == 11) and z < 8:
                ch = ch + " et"
            if num > 0:
                ch = ch + " " + self.tradd(num)
            else:
                ch = ch + self.tradd(num)
        return ch

    def tradn(self, num):
        global t1, t2
        ch = ""
        flagcent = False
        if num >= 1000000000:
            z = int(num / 1000000000)
            ch = ch + self.tradn(z) + " milliard"
            if z > 1:
                ch = ch + "s"
            num = num - z * 1000000000
        if num >= 1000000:
            z = int(num / 1000000)
            ch = ch + self.tradn(z) + " million"
            if z > 1:
                ch = ch + "s"
            num = num - z * 1000000
        if num >= 1000:
            if num >= 100000:
                z = int(num / 100000)
                if z > 1:
                    ch = ch + " " + self.tradd(z)
                ch = ch + " cent"
                flagcent = True
                num = num - z * 100000
                if int(num / 1000) == 0 and z > 1:
                    ch = ch + "s"
            if num >= 1000:
                z = int(num / 1000)
                if (z == 1 and flagcent) or z > 1:
                    ch = ch + " " + self.tradd(z)
                num = num - z * 1000
            ch = ch + " mille"
        if num >= 100:
            z = int(num / 100)
            if z > 1:
                ch = ch + " " + self.tradd(z)
            ch = ch + " cent"
            num = num - z * 100
            if num == 0 and z > 1:
                ch = ch + "s"
        if num > 0:
            ch = ch + " " + self.tradd(num)
        return ch

    def trad(self, nb, unite="dirham", decim="centime"):
        global t1, t2
        nb = round(nb, 2)
        t1 = [
            "",
            "un",
            "deux",
            "trois",
            "quatre",
            "cinq",
            "six",
            "sept",
            "huit",
            "neuf",
            "dix",
            "onze",
            "douze",
            "treize",
            "quatorze",
            "quinze",
            "seize",
            "dix-sept",
            "dix-huit",
            "dix-neuf",
        ]
        t2 = [
            "",
            "dix",
            "vingt",
            "trente",
            "quarante",
            "cinquante",
            "soixante",
            "septante",
            "quatre-vingt",
            "nonante",
        ]
        z1 = int(nb)
        z3 = (nb - z1) * 100
        z2 = int(round(z3, 0))
        if z1 == 0:
            ch = "zéro"
        else:
            ch = self.tradn(abs(z1))
        if z1 > 1 or z1 < -1:
            if unite != "":
                ch = ch + " " + unite + "s"
        else:
            ch = ch + " " + unite
        if z2 > 0:
            ch = ch + self.tradn(z2)
            if z2 > 1 or z2 < -1:
                if decim != "":
                    ch = ch + " " + decim + "s"
            else:
                ch = ch + " " + decim
        if nb < 0:
            ch = "moins " + ch
        return ch.upper()

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
    amount = fields.Monetary('Montant', currency_field='currency_id')
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
        for record in self:
            record.write({'state': 'posted'})
            if record.name == _('New'):
                record.write({'name': self.env['ir.sequence'].next_by_code('invoice.cash.payment') or _('New')})

    def action_cancel(self):
        self.write({'state': 'cancel'})

    def action_draft(self):
        self.write({'state': 'draft'})