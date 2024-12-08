# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import json
import logging
from datetime import timedelta
from collections import defaultdict

from odoo import api, fields, models, _
from odoo.tools import float_compare, float_round
from odoo.exceptions import UserError


_logger = logging.getLogger(__name__)


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    @api.depends('product_id', 'product_uom_qty', 'product_uom')
    def _compute_qty_at_date_m2(self):
        # able to commit the quantity anyway
        for line in self:
            qty = 0
            if line.product_id.id:
                line.env.cr.execute("""SELECT quantity FROM stock_quant WHERE product_id = %s AND location_id = 24 """, [line.product_id.id])
                results = line.env.cr.dictfetchall()
                for result in results:
                    qty = result.get('quantity')
            line.update({
                'free_qty_today_m2': qty
            })

    @api.depends('product_id', 'product_uom_qty', 'product_uom')
    def _compute_qty_at_date_DEPOT(self):
        # able to commit the quantity anyway
        for line in self:
            qty = 0
            if line.product_id.id:
                line.env.cr.execute("""SELECT quantity FROM stock_quant WHERE product_id = %s AND location_id = 18 """, [line.product_id.id])
                results = line.env.cr.dictfetchall()
                for result in results:
                    qty = result.get('quantity')
            line.update({
                'free_qty_today_DEPOT': qty
            })
    free_qty_today_m2 = fields.Float(compute='_compute_qty_at_date_m2', digits='Product Unit of Measure')
    free_qty_today_DEPOT = fields.Float(compute='_compute_qty_at_date_DEPOT', digits='Product Unit of Measure')
    
   