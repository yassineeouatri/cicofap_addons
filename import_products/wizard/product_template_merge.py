# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.exceptions import UserError
import logging

_logger = logging.getLogger(__name__)

class ProductMErge(models.TransientModel):
    _name = 'product.template.merge'
    _description = "Fusionner 2 produits"

    dest_product_id = fields.Many2one('product.template', 'Article à garder', required=True)
    src_product_id = fields.Many2one('product.template', 'Article à archiver', required=True)

    def action_merge(self):
        if self.dest_product_id == self.src_product_id:
            raise UserError(_("Impossible de fusionner 2 artciles identiques."))
        products_to_updates = []
        product_ids = self.env['product.product'].search([('product_tmpl_id', '=', self.dest_product_id.id)])
        _product_id = product_ids[0]
        for product_id in product_ids:
            if product_id != _product_id:
                products_to_updates.append(product_id)
        # get all products from src products to update
        product_ids = self.env['product.product'].search([('product_tmpl_id', '=', self.src_product_id.id)])
        for product_id in product_ids:
            products_to_updates.append(product_id)

        # update
        for product_id in products_to_updates:
            for table in ["purchase_order_line", "sale_order_line", "stock_move", "stock_move_line", "account_move_line"]:
                self._cr.execute("update {} set product_id={} where product_id={}".format(table, _product_id.id,
                                                                                          product_id.id))
            product_id.write({'active': False})
        # Archive src product template
        self.src_product_id.write({'active': False})
        return True
