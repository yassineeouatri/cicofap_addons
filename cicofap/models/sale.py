# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.exceptions import UserError
from datetime import  datetime, date
import calendar

current_year = datetime.now().year
start_date = datetime.strptime(f"{current_year}-01-01", "%Y-%m-%d").date()
end_date = datetime.strptime(f"{current_year}-12-31", "%Y-%m-%d").date()

import calendar

# Obtenir la date d'aujourd'hui
today = date.today()
# Date de début du mois
month_start_date = today.replace(day=1)
# Date de fin du mois
last_day = calendar.monthrange(today.year, today.month)[1]  # Retourne le dernier jour du mois
month_end_date = today.replace(day=last_day)

month_start_date_string = month_start_date.strftime('%Y-%m-%d')
month_end_date_string = month_end_date.strftime('%Y-%m-%d')

class SaleOrder(models.Model):
    _inherit = 'sale.order'
    _order = 'create_date desc, id desc'

    state = fields.Selection(selection_add=[('new', 'Etat brouillon')])
    payment_method = fields.Selection([('virement', 'Virement'), ('cheque', 'Chèque'), ('cash', 'Espèce'), ('traite', 'Traite')], 'Mode de paiement')
    no_payment = fields.Char('N° Payment')
    order_line = fields.One2many('sale.order.line', 'order_id', string='Order Lines',
                                 states={'cancel': [('readonly', True)], 'done': [('readonly', True)]}, copy=True,
                                 domain=[('route_id', '=', False)],
                                 auto_join=True)
    order_line_ti = fields.One2many('sale.order.line', 'order_id', string='Transferts Internes',
                                 states={'cancel': [('readonly', True)], 'done': [('readonly', True)]}, copy=True,
                                 domain = [('route_id', '!=', False)],
                                 auto_join=True)
    commercial_id = fields.Many2one('product.commercial', 'Commercial')
    transport_id = fields.Many2one('product.transport', 'Transport')
    devis_no = fields.Char('N° bon de commande')
    expedition = fields.Char('Expédition')
    cash_ids = fields.One2many('invoice.cash', 'order_id', 'Cashs')
    cash_count = fields.Integer(compute='_compute_cash_count', string='# Partenaires')
    invoice_status = fields.Selection(selection_add=[('cash', 'Cash')])
    show_cash_button = fields.Boolean(compute='_compute_show_cash_button')

    def _compute_show_cash_button(self):
        for order in self:
            if order.cash_ids:
                order.show_cash_button = True
            else:
                order.show_cash_button = False

    @api.depends('state', 'order_line.invoice_status', 'cash_ids')
    def _get_invoice_status(self):
        """
        Compute the invoice status of a SO. Possible statuses:
        - no: if the SO is not in status 'sale' or 'done', we consider that there is nothing to
          invoice. This is also the default value if the conditions of no other status is met.
        - to invoice: if any SO line is 'to invoice', the whole SO is 'to invoice'
        - invoiced: if all SO lines are invoiced, the SO is invoiced.
        - upselling: if all SO lines are invoiced or upselling, the status is upselling.
        """
        unconfirmed_orders = self.filtered(lambda so: so.state not in ['sale', 'done'])
        unconfirmed_orders.invoice_status = 'no'
        confirmed_orders = self - unconfirmed_orders
        if not confirmed_orders:
            return
        line_invoice_status_all = [
            (d['order_id'][0], d['invoice_status'])
            for d in self.env['sale.order.line'].read_group([
                ('order_id', 'in', confirmed_orders.ids),
                ('is_downpayment', '=', False),
                ('display_type', '=', False),
            ],
                ['order_id', 'invoice_status'],
                ['order_id', 'invoice_status'], lazy=False)]
        for order in confirmed_orders:
            print(1)
            line_invoice_status = [d[1] for d in line_invoice_status_all if d[0] == order.id]
            if order.state not in ('sale', 'done'):
                order.invoice_status = 'no'
            elif any(invoice_status == 'to invoice' for invoice_status in line_invoice_status):
                order.invoice_status = 'to invoice'
            elif line_invoice_status and all(invoice_status == 'invoiced' for invoice_status in line_invoice_status):
                order.invoice_status = 'invoiced'
            elif line_invoice_status and all(
                    invoice_status in ('invoiced', 'upselling') for invoice_status in line_invoice_status):
                order.invoice_status = 'upselling'
            else:
                order.invoice_status = 'no'
            if order.cash_ids:
                order.invoice_status = 'cash'

    @api.depends('cash_ids')
    def _compute_cash_count(self):
        for rec in self:
            rec.cash_count = len(rec.cash_ids)

    def action_quotation_validate(self):
        self.write({'state': 'draft'})

    def action_view_cash(self):
        self.ensure_one()
        action = self.env["ir.actions.actions"]._for_xml_id("cicofap.action_invoice_cash")
        action['domain'] = [('order_id', '=', self.id)]
        return action


class product_commercial(models.Model):
    _name = 'product.commercial'
    _description = "Commercials"
    _inherit = ['format.address.mixin', 'avatar.mixin']
    _order = "name"

    name = fields.Char('Commercial')
    # address fields
    street = fields.Char()
    street2 = fields.Char()
    zip = fields.Char(change_default=True)
    city = fields.Char()
    state_id = fields.Many2one("res.country.state", string='State', ondelete='restrict',
                               domain="[('country_id', '=?', country_id)]")
    country_id = fields.Many2one('res.country', string='Pays', ondelete='restrict')
    country_code = fields.Char(related='country_id.code', string="Code")
    partner_latitude = fields.Float(string='Geo Latitude', digits=(10, 7))
    partner_longitude = fields.Float(string='Geo Longitude', digits=(10, 7))
    email = fields.Char()
    email_formatted = fields.Char(
        'Formatted Email', compute='_compute_email_formatted',
        help='Format email address "Name <email@domain>"')
    phone = fields.Char()
    mobile = fields.Char()
    website = fields.Char('Siteweb')
    zone = fields.Char('Zone géographique')
    sale_order_ids = fields.One2many('sale.order', 'commercial_id', 'Ventes')
    sale_order_count = fields.Integer(compute='_compute_sale_order_count', string='# Sale Orders')
    invoice_count = fields.Integer(string='Invoice Count', compute='_compute_invoice_count')
    total = fields.Monetary(compute='_compute_invoice_total', string="Total")
    total_payed = fields.Monetary(compute='_compute_invoice_total', string="Total Invoiced")
    total_invoiced = fields.Monetary(compute='_compute_invoice_total', string="Total Invoiced")
    total_invoiced_payed = fields.Monetary(compute='_compute_invoice_total', string="Total Invoiced Payed")
    total_cashed = fields.Monetary(compute='_compute_invoice_total', string="Total Cashed")
    total_cash_payed = fields.Monetary(compute='_compute_invoice_total', string="Total Cash Payed")
    currency_id = fields.Many2one('res.currency', compute='_get_company_currency', readonly=True, string="Currency")

    def action_view_sale_order(self):
        self.ensure_one()
        action = self.env["ir.actions.actions"]._for_xml_id("sale.action_quotations_with_onboarding")
        action['domain'] = [('commercial_id', '=', self.id),
                            ('date_order', '>=', f'{current_year}-01-01'),
                            ('date_order', '<=', f'{current_year}-12-31')]
        return action

    def action_view_sale_order_month(self):
        self.ensure_one()
        action = self.env["ir.actions.actions"]._for_xml_id("sale.action_quotations_with_onboarding")
        action['domain'] = [('commercial_id', '=', self.id),
                            ('date_order', '>=', month_start_date_string),
                            ('date_order', '<=', month_end_date_string)]
        return action

    def action_view_payment(self):
        self.ensure_one()
        action = self.env["ir.actions.actions"]._for_xml_id("account.action_account_payments")
        ids = []
        for partner in self.partner_ids:
            ids.append((partner.id))
        action['domain'] = [('partner_id', '=', ids)]
        return action

    @api.depends('sale_order_ids')
    def _compute_sale_order_count(self):
        for partner in self:
            count = 0
            for order in partner.sale_order_ids:
                if order.date_order and month_start_date <= order.date_order.date() <= month_end_date:
                    count += 1
            partner.sale_order_count = count

    @api.depends('sale_order_ids')
    def _compute_invoice_count(self):
        for record in self:
            count = 0
            _invoices = []
            for order in record.sale_order_ids:
                invoices = order.order_line.invoice_lines.move_id.filtered(
                    lambda r: r.move_type in ('out_invoice', 'out_refund'))
                _invoices.extend(invoices)
            record.invoice_count = len(_invoices)

    @api.depends('sale_order_ids')
    def _compute_invoice_total(self):
        for record in self:
            total = 0
            total_invoiced = 0
            total_invoiced_payed = 0
            month_total_invoiced = 0
            month_total_invoiced_payed = 0
            year_total_invoiced = 0
            year_total_invoiced_payed = 0

            _invoices = []
            for order in record.sale_order_ids:
                invoices = order.order_line.invoice_lines.move_id.filtered(
                    lambda r: r.move_type in ('out_invoice', 'out_refund'))
                _invoices.extend(invoices)
            for _invoice in _invoices:
                for _invoice_line in _invoice.invoice_line_ids:
                    total_invoiced += _invoice_line.price_total
            # compute total invoiced monthly
            _invoices = []
            for order in record.sale_order_ids:
                if order.date_order and month_start_date <= order.date_order.date() <= month_end_date:
                    invoices = order.order_line.invoice_lines.move_id.filtered(
                        lambda r: r.move_type in ('out_invoice', 'out_refund'))
                    _invoices.extend(invoices)
            for _invoice in _invoices:
                for _invoice_line in _invoice.invoice_line_ids:
                    month_total_invoiced += _invoice_line.price_total

            # compute total invoiced year
            _invoices = []
            for order in record.sale_order_ids:
                if order.date_order and start_date <= order.date_order.date() <= end_date:
                    invoices = order.order_line.invoice_lines.move_id.filtered(
                        lambda r: r.move_type in ('out_invoice', 'out_refund'))
                    _invoices.extend(invoices)
            for _invoice in _invoices:
                for _invoice_line in _invoice.invoice_line_ids:
                    year_total_invoiced += _invoice_line.price_total

            for partner in self.partner_ids:
                for payment in self.env['account.payment'].search([('partner_id', '=', partner.id), ('state', '=', 'posted')]):
                    if payment.invoice_date and month_start_date <= payment.invoice_date <= month_end_date:
                        month_total_invoiced_payed += payment.amount
                    if payment.invoice_date and start_date <= payment.invoice_date <= end_date:
                        year_total_invoiced_payed += payment.amount
                    total_invoiced_payed += payment.amount

            total_cashed = 0
            month_total_cashed = 0
            month_total_cash_payed = 0
            year_total_cashed = 0
            year_total_cash_payed = 0
            total_cash_payed = 0
            _cashs = []
            for order in self.sale_order_ids:
                for cash in order.cash_ids:
                    _cashs.append(cash)
            for _cash in _cashs:
                if _cash.state == 'done':
                    if _cash.date and month_start_date <= _cash.date <= month_end_date:
                        month_total_cashed += _cash.price_total
                        month_total_cash_payed += _cash.price_payed
                    if _cash.date and start_date <= _cash.date <= end_date:
                        year_total_cashed += _cash.price_total
                        year_total_cash_payed += _cash.price_payed
                    total_cashed += _cash.price_total
                    total_cash_payed += _cash.price_payed

            record.total_invoiced = month_total_invoiced
            record.total_invoiced_payed = month_total_invoiced_payed
            record.total_cashed = month_total_cashed
            record.total_cash_payed = month_total_cash_payed
            record.total = year_total_invoiced + year_total_cashed
            record.total_payed = year_total_invoiced_payed + year_total_cash_payed

    def action_view_invoice(self):
        self.ensure_one()
        _invoices = []
        for order in self.sale_order_ids:
            if order.date_order and month_start_date <= order.date_order.date() <= month_end_date:
                invoices = order.order_line.invoice_lines.move_id.filtered(
                    lambda r: r.move_type in ('out_invoice', 'out_refund'))
                _invoices.extend(invoices)
        invoice_ids = [_invoice.id for _invoice in _invoices]
        result = {
            "type": "ir.actions.act_window",
            "res_model": "account.move",
            "domain": [('id', 'in', invoice_ids)],
            "context": {"create": False},
            "name": "Factures",
            'view_mode': 'tree,form',
        }
        return result

    def action_view_cash(self):
        self.ensure_one()
        action = self.env["ir.actions.actions"]._for_xml_id("cicofap.action_invoice_cash")
        _cashs = []
        for order in self.sale_order_ids:
            for cash in order.cash_ids:
                if cash.date and month_start_date <= cash.date <= month_end_date:
                    _cashs.append(cash)
        cash_ids = [_cash.id for _cash in _cashs]
        action['domain'] = [('id', 'in', cash_ids)]
        action['context'] = {'search_default_filter_current_month': True, 'search_default_filter_done': True}
        return action

    def action_view_cash_payments(self):
        self.ensure_one()
        action = self.env["ir.actions.actions"]._for_xml_id("cicofap.action_invoice_cash_payment")
        _cashs = []
        for order in self.sale_order_ids:
            for cash in order.cash_ids:
                if cash.date and month_start_date <= cash.date <= month_end_date:
                    _cashs.append(cash)
        cash_ids = [_cash.id for _cash in _cashs]
        action['domain'] = [('cash_id', 'in', cash_ids)]
        action['context'] = {'search_default_filter_current_month': True, 'search_default_filter_posted': True}
        return action

    def _get_company_currency(self):
        for record in self:
            record.currency_id = self.env.company.currency_id


class product_transport(models.Model):
    _name = 'product.transport'
    _description = "Transport"
    _order = "name"

    name = fields.Char('Transport')


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    location_id = fields.Many2one('stock.location', 'Location')
    warehouse_id = fields.Many2one('stock.warehouse', 'Warehouse')
    price_taxinc = fields.Monetary(compute='_compute_price_taxinc', string='Price Unitaire TTC',
                                          store=True)

    @api.depends('price_unit', 'tax_id')
    def _compute_price_taxinc(self):
        """
        Compute the amounts of the SO line.
        """
        for line in self:
            price = line.price_unit
            taxes = line.tax_id.compute_all(price, line.order_id.currency_id, 1,
                                            product=line.product_id, partner=line.order_id.partner_shipping_id)
            line.update({
                'price_taxinc': taxes['total_included']
            })

    @api.onchange('route_id')
    def onchange_route_id(self):
        if self.route_id:
            self.price_unit = 0.0

    @api.onchange('price_unit')
    def onchange_route_id(self):
        if self.route_id:
            self.price_unit = 0.0

    @api.onchange('product_uom', 'product_uom_qty')
    def product_uom_change(self):
        if self.order_id.pricelist_id and self.order_id.partner_id:
            product = self.product_id.with_context(
                lang=self.order_id.partner_id.lang,
                partner=self.order_id.partner_id,
                quantity=self.product_uom_qty,
                date=self.order_id.date_order,
                pricelist=self.order_id.pricelist_id.id,
                uom=self.product_uom.id,
                fiscal_position=self.env.context.get('fiscal_position')
            )

