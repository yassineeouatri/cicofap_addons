# -*- coding: utf-8 -*-
from collections import defaultdict
from lxml import etree

from odoo import models, fields, api, _
from odoo.exceptions import UserError
from odoo.tools import float_compare, frozendict


class AccountPaymentRegister(models.TransientModel):
    _inherit = 'account.payment.register'

    payment_method = fields.Selection(
        [('virement', 'Virement'), ('cheque', 'Chèque'), ('cash', 'Espèce'), ('traite', 'Traite')], 'Mode de paiement')
    no_payment = fields.Char('N° Payment')
    payment_file = fields.Binary(string="Fichier")
    payment_filename = fields.Char("Nom du fichier")

    def _create_payment_vals_from_wizard(self):
        payment_vals = {
            'date': self.payment_date,
            'amount': self.amount,
            'payment_type': self.payment_type,
            'partner_type': self.partner_type,
            'ref': self.communication,
            'payment_method': self.payment_method,
            'no_payment': self.no_payment,
            'payment_file': self.payment_file,
            'payment_filename': self.payment_filename,
            'journal_id': self.journal_id.id,
            'currency_id': self.currency_id.id,
            'partner_id': self.partner_id.id,
            'partner_bank_id': self.partner_bank_id.id,
            'payment_method_line_id': self.payment_method_line_id.id,
            'destination_account_id': self.line_ids[0].account_id.id
        }

        if not self.currency_id.is_zero(self.payment_difference) and self.payment_difference_handling == 'reconcile':
            payment_vals['write_off_line_vals'] = {
                'name': self.writeoff_label,
                'amount': self.payment_difference,
                'account_id': self.writeoff_account_id.id,
            }
        return payment_vals

class AccountPayment(models.Model):
    _inherit = 'account.payment'

    payment_method = fields.Selection(
        [('virement', 'Virement'), ('cheque', 'Chèque'), ('cash', 'Espèce'), ('traite', 'Traite')],
        'Mode de paiement')
    no_payment = fields.Char('N° Payment')
    payment_file = fields.Binary(string="Fichier")
    payment_filename = fields.Char("Nom du fichier")

class AccountMove(models.Model):
    _inherit = 'account.move'

    name = fields.Char(string='Number', copy=False, compute='_compute_name', inverse='_set_name', readonly=False,
                       store=True, index=True, tracking=True)
    montant_text = fields.Text(
        compute="_compute_amount_text", string="Montant", readonly=True, store=True
    )

    @api.depends('amount_total', 'currency_id')
    def _compute_amount_text(self):
        for record in self:
            record.montant_text = self.trad(record.amount_total, record.currency_id.currency_unit_label,
                                            record.currency_id.currency_subunit_label)

    def _set_name(self):
        for record in self:
            # Your custom logic to handle writes to the compute field
            pass

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
