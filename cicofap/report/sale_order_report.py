from odoo import models, api
from datetime import  datetime
import logging

_logger = logging.getLogger(__name__)

class SaleOrderPrintReport(models.AbstractModel):
    _name = 'report.cicofap.report_sale_order_print'
    _description = "Sales Order Report Print"

    def get_invs(self, date_from, date_to):
        invs = []
        orders = self.env['sale.order'].search([('partner_id', '=', data['partner_id'])], order='date_order ASC')
        pickings = self.env['stock.picking'].search([('name', 'like', 'OUT'),
                                                     ('partner_id', '=', data['partner_id']),
                                                     ('state', '=', 'done')])
        for picking in pickings:
            for order in orders:
                if order.name == picking.origin:
                    invoices = order.order_line.invoice_lines.move_id.filtered(
                        lambda r: r.move_type in ('out_invoice', 'out_refund'))
                    ids = []
                    for invoice in invoices:
                        ids.append(invoice.id)
                    invs.extend(invoices.search([('id', 'in', ids),
                                    ('invoice_date', '>=', datetime.strftime(date_from,'%Y-%m-%d 00:00:00')),
                                     ('invoice_date', '<=', datetime.strftime(date_to, '%Y-%m-%d 23:59:59')),]))
        return invoices

    def get_invoices(self, order, date_from, date_to):
        invoices = order.order_line.invoice_lines.move_id.filtered(
            lambda r: r.move_type in ('out_invoice', 'out_refund'))
        ids = []
        for invoice in invoices:
            ids.append(invoice.id)
        invoices = invoices.search([('id', 'in', ids),
                                    ('state', '=', 'posted'),
                        ('invoice_date', '>=', datetime.strftime(date_from,'%Y-%m-%d 00:00:00')),
                         ('invoice_date', '<=', datetime.strftime(date_to, '%Y-%m-%d 23:59:59')),])
        return invoices

    def get_cashs(self, order, date_from, date_to):
        invoices = self.env['invoice.cash'].search([('order_id', '=', order.id), ('state', '=', 'done'),
                        ('date', '>=', datetime.strftime(date_from,'%Y-%m-%d 00:00:00')),
                        ('date', '<=', datetime.strftime(date_to, '%Y-%m-%d 23:59:59')),])
        return invoices

    def get_quantity(self, picking):
        quantity = 0
        for obj in picking.move_ids_without_package:
            quantity += obj.quantity_done
        return int(quantity)
    @api.model
    def _get_report_values(self, docids, data=None):
        print(data)
        moves = self.env['account.move'].search([('partner_id', '=', data['partner_id']), ('state', '=', 'posted'),])
        pickings = self.env['stock.picking'].search([('name', 'like', 'OUT'),
                                                     ('partner_id', '=', data['partner_id']),
                                                     ('state', '=', 'done')])
        if data['warehouse_id']:
            orders = self.env['sale.order'].search([('partner_id', '=', data['partner_id']), ('warehouse_id', '=', data['warehouse_id'])], order='date_order ASC')
        else:
            orders = self.env['sale.order'].search([('partner_id', '=', data['partner_id'])], order='date_order ASC')

        lines = []
        for order in orders:
            for picking in pickings:
                if order.name == picking.origin:
                    print(order.name)
                    if data['type'] == 'invoice':
                        invoices = self.get_invoices(order, datetime.strptime(data['date_from'], '%Y-%m-%d'), datetime.strptime(data['date_to'], '%Y-%m-%d'))
                        for invoice in invoices:
                            if invoice.amount_total_signed >= 0:
                                bl_name = picking.name
                                bl_date = datetime.strftime(picking.scheduled_date, '%Y/%m/%d')
                                amount_untaxed = order.amount_untaxed
                                amount_total = order.amount_total
                            else:
                                bl_name = invoice.name
                                bl_date = datetime.strftime(invoice.invoice_date, '%Y/%m/%d')
                                invoice.amount_untaxed_signed
                                amount_untaxed = invoice.amount_untaxed_signed
                                amount_total = invoice.amount_total_signed
                            line = {
                                'name': order.name,
                                'bl_name': bl_name,
                                'bl_date': bl_date,
                                'amount_untaxed_signed': amount_untaxed,
                                'amount_total_signed': amount_total,
                                'quantity': self.get_quantity(picking)
                            }
                            lines.append(line)
                    else:
                        invoices = self.get_cashs(order, datetime.strptime(data['date_from'], '%Y-%m-%d'),
                                                     datetime.strptime(data['date_to'], '%Y-%m-%d'))
                        for invoice in invoices:
                            bl_name = picking.name
                            bl_date = datetime.strftime(picking.scheduled_date, '%Y/%m/%d')
                            amount_untaxed = order.price_total
                            amount_total = order.price_total
                            line = {
                                'name': order.name,
                                'bl_name': bl_name,
                                'bl_date': bl_date,
                                'amount_untaxed_signed': amount_untaxed,
                                'amount_total_signed': amount_total,
                                'quantity': self.get_quantity(picking)
                            }
                            lines.append(line)
        print(lines)
        lines = sorted(lines, key=lambda d: d['bl_date'], reverse=False)

        return {
            'doc_ids': docids,
            'doc_model': 'sale.order.print',
            'docs': self.env['res.company'].browse(self.env.company.id),
            'company_id': self.env['res.company'].browse(self.env.company.id),
            'partner_id': self.env['res.partner'].search([('id','=',data['partner_id'])]),
			'date_from': datetime.strftime(datetime.strptime(data['date_from'], '%Y-%m-%d'), '%d/%m/%Y'),
            'date_to':datetime.strftime(datetime.strptime(data['date_to'], '%Y-%m-%d'), '%d/%m/%Y'),
            'lines': lines
        }