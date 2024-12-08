# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _


class stock_picking(models.Model):
    _inherit = 'stock.picking'
    _order = "priority desc, scheduled_date desc, id desc"


    visibility = fields.Boolean(compute="compute_vasibility")
    warehouse = fields.Char(related='picking_type_id.warehouse_id.name', readonly=True)
    location_id = fields.Many2one(
        'stock.location', "Source Location",
        default=lambda self: self.env['stock.picking.type'].browse(
            self._context.get('default_picking_type_id')).default_location_src_id,
        check_company=True, readonly=True, required=True,
        states={'draft': [('readonly', False)], 'assigned': [('readonly', False)]})
    location_dest_id = fields.Many2one(
        'stock.location', "Destination Location",
        default=lambda self: self.env['stock.picking.type'].browse(
            self._context.get('default_picking_type_id')).default_location_dest_id,
        check_company=True, readonly=True, required=True,
        states={'draft': [('readonly', False)], 'assigned': [('readonly', False)]})

    def compute_vasibility(self):
        status = False
        if self.picking_type_code == 'internal':
            if self.env.user.has_group('cicofap.group_cicofap_depot') and (self.state in ('waiting','confirmed') or self.show_validate) :
                    status = True
        else:
            if (self.state in ('waiting', 'confirmed') or self.show_validate):
                status = True
        self.visibility = status

    def do_print_picking(self):
        res = super(stock_picking, self).do_print_picking()
        self.write({'printed': True})
        return self.env.ref('stock.action_report_delivery').report_action(self)


class StockQuant(models.Model):
    _inherit = 'stock.quant'

    @api.model
    def action_view_quants_depot(self):
        self = self._set_view_context()
        return self._get_quants_action(domain=[('location_id.complete_name','=', 'DEPOT/Stock')], extend=True)

    @api.model
    def action_view_quants_m1(self):
        self = self._set_view_context()
        return self._get_quants_action(domain=[('location_id.complete_name', '=', 'M1/Stock')], extend=True)

    @api.model
    def action_view_quants_siege(self):
        self = self._set_view_context()
        return self._get_quants_action(domain=[('location_id.complete_name', '=', 'SIEGE/Stock')], extend=True)
