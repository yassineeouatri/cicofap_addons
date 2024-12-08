# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models, tools


class ProductMovement(models.Model):

    _name = "product.movement.report"
    _description = "Product Movement Report"
    _order = 'date_order desc'
    _auto = False

    type = fields.Char('Type', readonly=True)
    product_id = fields.Many2one('product.product', string='Article', readonly=True)
    partner_id = fields.Many2one('res.partner', string='Client/Fournisseur', readonly=True)
    order_name = fields.Char('Commande', readonly=True)
    date_order = fields.Date("Date Commande", readonly=True)
    date_transfert = fields.Date("Date Transfert", readonly=True)
    purchase_price = fields.Float('Prix de Vente/Achat', readonly=True),
    transfert_name = fields.Char('Transfert', readonly=True)
    price_unit = fields.Float('Prix Unitaire', readonly=True)
    price_subtotal = fields.Float('Prix HT Total', readonly=True)
    price_total = fields.Float('Prix TTC Total', readonly=True)
    quantity = fields.Integer('Quantité', readonly=True)
    location_dest_id = fields.Many2one('stock.location', 'A', readonly=True)
    location_id = fields.Many2one('stock.location', 'De', readonly=True)
    margin_percent = fields.Float("Margin (%)")

    def init(self):
        tools.drop_view_if_exists(self._cr, 'product_movement_report')

        self._cr.execute("""
            CREATE or REPLACE view product_movement_report as (
               SELECT ROW_NUMBER() OVER () AS id, * FROM(
                SELECT 'Vente' as type, so.name as order_name,so.date_order,so.partner_id,sol.price_subtotal,sol.price_total,sol.product_uom_qty as quantity,sol.price_unit,sol.currency_id,sol.product_id,st.name as transfert_name,date(st.date) as date_transfert,
                st.location_id,st.location_dest_id,sol.margin_percent
                FROM sale_order so
                INNER JOIN sale_order_line sol on so.id=sol.order_id
                INNER JOIN product_product pp on pp.id=sol.product_id
                INNER JOIN product_template pt on pt.id=pp.product_tmpl_id
                INNER JOIN stock_picking st on so.name = st.origin
                UNION
                SELECT 'Achat' as type,so.name as order_name,so.date_order,so.partner_id,sol.price_subtotal,sol.price_total,sol.product_uom_qty as quantity,sol.price_unit,sol.currency_id,sol.product_id,st.name,date(st.date) as date_transfert,
                st.location_id,st.location_dest_id,0
                FROM purchase_order so
                INNER JOIN purchase_order_line sol on so.id=sol.order_id
                INNER JOIN product_product pp on pp.id=sol.product_id
                INNER JOIN product_template pt on pt.id=pp.product_tmpl_id
                INNER JOIN stock_picking st on so.name = st.origin
				UNION				
				SELECT 'Retour' as type, sp.name, sp.date, sp.partner_id,0,0,product_qty,0,1,product_id,sp.name,date(sp.date) as date_transfert,
				sp.location_id,sp.location_dest_id,0
				FROM stock_picking sp
				INNER JOIN stock_move sm on sm.picking_id=sp.id
				WHERE sp.name LIKE '%RET%'
				) AS t
            );
        """)

