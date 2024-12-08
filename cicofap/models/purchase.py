# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _

class PurchaseOrders(models.Model):
    _name = 'purchase.order'
    _inherit = 'purchase.order'

    def button_cancel2(self):
        for order in self:
            for inv in order.invoice_ids:
                if inv and inv.state not in ('cancel', 'draft'):
                    raise UserError(_("Unable to cancel this purchase order. You must first cancel the related vendor bills."))
            # If the product is MTO, change the procure_method of the closest move to purchase to MTS.
            # The purpose is to link the po that the user will manually generate to the existing moves's chain.
            print('bb')
            for order_line in order.order_line:
                order_line.move_ids._action_cancel()
                if order_line.move_dest_ids:
                    move_dest_ids = order_line.move_dest_ids
                    if order_line.propagate_cancel:
                        move_dest_ids._action_cancel()
                    else:
                        move_dest_ids.write({'procure_method': 'make_to_stock'})
                        move_dest_ids._recompute_state()

            for pick in order.picking_ids.filtered(lambda r: r.state != 'cancel'):
                pick.action_cancel()

            order.order_line.write({'move_dest_ids': [(5, 0, 0)]})

        self.write({'state': 'cancel', 'mail_reminder_confirmed': False})

class PurchaseOrder(models.Model):
    _name = 'purchase.order.line'
    _inherit = 'purchase.order.line'

    coefficient = fields.Float('Coefficient')
    purchase_price = fields.Float(string='Coût', compute="_compute_purchase_price",store=True, readonly=True)
    ht_price = fields.Float(string='Prix HT', compute="_compute_purchase_price",store=True, readonly=True)
    ttc_price = fields.Float(string='Prix TTC', compute="_compute_purchase_price",store=True, readonly=True)

    @api.depends('product_id', 'coefficient', 'price_unit')
    def _compute_purchase_price(self):
        for line in self:
            if not line.product_id:
                line.purchase_price = 0.0
                continue
            line.purchase_price = line.product_id.standard_price
            line.ttc_price = round(line.price_unit * line.coefficient, 2)
            line.ht_price = round(line.ttc_price/1.2, 2)

    @api.onchange('ht_price', 'product_id')
    def onchange_ht_price(self):
        if self.ht_price and self.product_id:
            product_id = self.env['product.product'].search([('id', '=', self.product_id.id)])
            product_id.write({'standard_price': self.ht_price})


    def _get_product_purchase_description(self, product_lang):
        res = super(PurchaseOrder, self)._get_product_purchase_description(product_lang)
        self.ensure_one()
        name = product_lang.name
        if product_lang.description_purchase:
            name += '\n' + product_lang.description_purchase

        return name