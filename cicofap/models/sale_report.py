# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models


class SaleReport(models.Model):
    _inherit = "sale.report"

    commercial_id = fields.Many2one('product.commercial', 'Commercial', readonly=True)

    def _query(self, with_clause='', fields={}, groupby='', from_clause=''):
        fields['commercial_id'] = ", s.commercial_id as commercial_id"
        groupby += ', s.commercial_id'
        return super(SaleReport, self)._query(with_clause, fields, groupby, from_clause)