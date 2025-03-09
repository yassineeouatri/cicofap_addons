# -*- coding: utf-8 -*-
##############################################################################
#
#    ODOO, Open Source Management Solution
#    Copyright (C) 2017 NEXTMA (<nextma.com>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
import calendar
from odoo import models, fields, api
from datetime import  datetime, date
current_year = datetime.now().year
year_start_date = datetime.strptime(f"{current_year}-01-01", "%Y-%m-%d").date()
year_end_date = datetime.strptime(f"{current_year}-12-31", "%Y-%m-%d").date()

# Obtenir la date d'aujourd'hui
today = date.today()
# Date de début du mois
month_start_date = today.replace(day=1)
# Date de fin du mois
last_day = calendar.monthrange(today.year, today.month)[1]  # Retourne le dernier jour du mois
month_end_date = today.replace(day=last_day)

month_start_date_string = month_start_date.strftime('%Y-%m-%d')
month_end_date_string = month_end_date.strftime('%Y-%m-%d')

class ResPartner(models.Model):
    _inherit = "res.partner"

    solde_ids = fields.One2many('res.partner.solde', 'partner_id', 'Soldes')
    currency_id = fields.Many2one('res.currency', compute='_get_company_currency', readonly=True,
                                  string="Currency", help='Utility field to express amount currency')
    x_solde_cash_init = fields.Float('Report Initial Cash')
    x_solde_invoice_init = fields.Float('Report Initial Facture')
    x_solde_init = fields.Float('Report Initial Facture')
    total_payed = fields.Monetary(compute='_payment_total', string="Total Payé")
    x_total_invoiced = fields.Monetary(compute='_payment_total', string="Total Facturé TTC")
    x_total_residual = fields.Monetary(compute='_payment_total', string="Total restant TTC")
    x_total_cashed = fields.Monetary(compute='_cash_total', string="Total cash TTC")
    x_total_cashed_payed = fields.Monetary(compute='_cashs_total', string="Total cash payé TTC")
    x_solde_cash = fields.Monetary(compute='_payment_total', string="Report final Cash")
    x_solde_invoice = fields.Monetary(compute='_payment_total', string="Report final Facture")
    solde = fields.Monetary(compute='_payment_total', string="Report final Facture")

    def _compute_sale_order_count(self):
        # retrieve all children partners and prefetch 'parent_id' on them
        all_partners = self.with_context(active_test=False).search([('id', 'child_of', self.ids)])
        all_partners.read(['parent_id'])

        sale_order_groups = self.env['sale.order'].read_group(
            domain=[('partner_id', 'in', all_partners.ids)],
            fields=['partner_id'], groupby=['partner_id']
        )
        partners = self.browse()
        for group in sale_order_groups:
            partner = self.browse(group['partner_id'][0])
            while partner:
                if partner in self:
                    partner.sale_order_count += group['partner_id_count']
                    partners |= partner
                partner = partner.parent_id
        (self - partners).sale_order_count = 0

    def action_view_partner_invoices(self):
        self.ensure_one()
        action = self.env["ir.actions.actions"]._for_xml_id("account.action_move_out_invoice_type")
        action['domain'] = [
            ('move_type', 'in', ('out_invoice', 'out_refund')),
            ('partner_id', 'child_of', self.id),
        ]
        action['context'] = {'default_move_type':'out_invoice', 'move_type':'out_invoice', 'journal_type': 'sale', 'search_default_open': 1}
        return action

    def action_view_partner_payments(self):
        self.ensure_one()
        action = self.env["ir.actions.actions"]._for_xml_id("account.action_account_payments")
        payment_ids = []
        payments = self.env['account.payment'].search([('partner_id', '=', self.id)])
        for payment in payments:
            if payment.date and month_start_date <= payment.date <= month_end_date:
                payment_ids.append(payment.id)
        action['domain'] = [('id', 'in', payment_ids)]
        return action

    def action_view_partner_moves(self):
        self.ensure_one()
        action = self.env["ir.actions.actions"]._for_xml_id("account.action_move_out_invoice_type")
        invoice_ids = []
        moves = self.env['account.move'].search(
            [('partner_id', '=', self.id), ('state', 'not in', ['draft', 'cancel']),
             ('move_type', 'in', ('out_invoice', 'out_refund'))])
        for move in moves:
            if move.invoice_date and month_start_date <= move.invoice_date <= month_end_date:
                invoice_ids.append(move.id)
        print(invoice_ids)
        result = {
            "type": "ir.actions.act_window",
            "res_model": "account.move",
            "domain": [('id', 'in', invoice_ids)],
            "context": {"create": False},
            "name": "Factures",
            'view_mode': 'tree,form',
        }
        return result

    def action_view_partner_cashs(self):
        self.ensure_one()
        action = self.env["ir.actions.actions"]._for_xml_id("cicofap.action_invoice_cash")
        action['domain'] = [('partner_id', 'child_of', self.id)]
        action['context'] = {'search_default_filter_current_month': True, 'search_default_filter_done': True}
        return action

    def action_view_partner_cash_payments(self):
        self.ensure_one()
        action = self.env["ir.actions.actions"]._for_xml_id("cicofap.action_invoice_cash_payment")
        cash_ids_obj = self.env['invoice.cash'].search([('partner_id', 'child_of', self.id)])
        cash_ids = [cash.id for cash in cash_ids_obj]
        action['domain'] = [('cash_id', 'in', cash_ids)]
        action['context'] = {'search_default_filter_current_month': True, 'search_default_filter_posted': True}
        return action

    def _invoice_total(self):
        for record in self:
            total_invoiced = 0
            total_residual = 0
            moves = self.env['account.move'].search([('partner_id', '=', record.id),
                                                     ('state', 'not in', ['draft', 'cancel']),
                                                     ('move_type', 'in', ('out_invoice', 'out_refund'))])
            for move in moves:
                if move.invoice_date and month_start_date <= move.invoice_date.date() <= month_end_date:
                    total_invoiced += move.price_total
                    total_residual += move.amount_residual

            record.x_total_invoiced = total_invoiced
            record.x_total_residual = total_residual

    def _payment_total(self):
        for record in self:
            total_payed = 0
            total_invoiced = 0
            total_residual = 0
            payments = self.env['account.payment'].search([('partner_id', '=', record.id)])
            for payment in payments:
                if payment.date and month_start_date <= payment.date <= month_end_date:
                    total_payed += payment.amount

            moves = self.env['account.move'].search(
                [('partner_id', '=', record.id), ('state', 'not in', ['draft', 'cancel']),
                 ('move_type', 'in', ('out_invoice', 'out_refund'))])
            for move in moves:
                if move.invoice_date and month_start_date <= move.invoice_date <= month_end_date:
                    total_invoiced += move.amount_total
                    total_residual += move.amount_residual

            record.x_total_invoiced = total_invoiced
            record.total_payed = total_payed
            record.x_solde_invoice = record.x_total_invoiced + record.x_solde_invoice_init - record.total_payed
            record.x_solde_cash = record.x_total_cashed + record.x_solde_cash_init - record.x_total_cashed_payed
            record.solde = record.x_solde_invoice + record.x_solde_cash

    def _cash_total(self):
        for record in self:
            total_cashed = 0
            month_total_cashed = 0
            month_total_cash_payed = 0
            year_total_cashed = 0
            year_total_cash_payed = 0
            total_cash_payed = 0
            _cashs = self.env['invoice.cash'].search([('partner_id', '=', record.id)])
            for _cash in _cashs:
                if _cash.state == 'done':
                    if _cash.date and month_start_date <= _cash.date <= month_end_date:
                        month_total_cashed += _cash.price_total
                        month_total_cash_payed += _cash.price_payed
                    if _cash.date and year_start_date <= _cash.date <= year_end_date:
                        year_total_cashed += _cash.price_total
                        year_total_cash_payed += _cash.price_payed
                    total_cashed += _cash.price_total
                    total_cash_payed += _cash.price_payed
            record.x_total_cashed = month_total_cashed
            record.x_total_cashed_payed = month_total_cash_payed


class ResPartnerSolde(models.Model):
    _name = "res.partner.solde"
    _description = "Solde"

    partner_id = fields.Many2one('res.partner', 'Client')
    to_pay = fields.Float('Montant à payer')
    payed = fields.Float('Montant Payé')
    diff = fields.Float(string='Différence', compute="_compute_diff", store=True, readonly=True)

    @api.depends('to_pay', 'payed')
    def _compute_diff(self):
        for line in self:
            line.diff = line.payed - line.to_pay


