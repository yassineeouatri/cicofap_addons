from odoo import api, fields, models


class SaleOrder(models.Model):
    _inherit = "sale.order"

    cancel_done_picking = fields.Boolean(string='Cancel Done Delivery?', compute='check_cancel_done_picking')

    @api.model
    def check_cancel_done_picking(self):
        for order in self:
            Flag = False
            if self.user_has_groups('stock_picking_cancel_cs.group_cancel_delivery_order'):
                for picking in self.picking_ids:
                    if picking.state != 'cancel':
                        Flag = True
                        break
            order.cancel_done_picking = Flag
                

    def cancel_picking(self):
        if len(self.picking_ids) == 1 :
            self.picking_ids.with_context({'Flag':True}).action_cancel()
            return self.action_view_picking()
        else:
            return self.action_cancel_selected_picking()
        
    def action_view_picking(self):
        action = self.env.ref('stock.action_picking_tree_all').read()[0]
        picking_records = self.mapped('picking_ids')
        if picking_records:
            action['views'] = [(self.env.ref('stock.view_picking_form').id, 'form')]
            action['res_id'] = picking_records.id
        return action

    def action_cancel_selected_picking(self):
        action = self.env.ref('stock_picking_cancel_cs.action_cancel_delivery_cft').read()[0]
        picking_obj=self.env['stock.picking']
        pickings=[]
        for picking in self.picking_ids:
            if picking.state !='cancel':
                pickings.append(picking.id)

        action['context'] ={ 'pickings':pickings }
        return action
        {
            'type': 'ir.actions.act_window',
            'res_model': 'cancel.picking.wizard',
            'view_mode':'form',
            'views': [(self.env.ref('stock_picking_cancel_cs.delivery_cancel_form_cft').id, 'form')],
            'target': 'new',
            'context': {
                    'pickings':pickings,
            },
        }
