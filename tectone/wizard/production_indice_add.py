# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
from odoo import api, models, fields
from datetime import datetime


class production_document_indice_add(models.Model):
    _name = 'production.document.indice.add'

    document_id = fields.Many2one('production.document', 'Document', required=True, ondelete='cascade')
    no_indice = fields.Integer('Nb indices', default=1, required=True)

    def action_done(self):
        indice = -1
        document_indice_obj = self.env['production.document.indice'].search([('document_id', '=', self.document_id.id)],
                                                                            order='indice desc', limit=1)
        if document_indice_obj:
            indice = int(document_indice_obj.indice)

        document_obj = self.env['production.document'].search([('id', '=', self.document_id.id)])
        if self.document_id.state == 'draft':
            document_obj.write({'indice': "{:02d}".format(indice + 1)})

            document_indice_ids = self.env['production.document.indice'].search(
                [('document_id', '=', self.document_id.id)])
            for record in document_indice_ids:
                record.write({'actif': False})

            self.env['production.document.indice'].create({'document_id': self.document_id.id,
                                                           'date': datetime.today(),
                                                           'nature': '*',
                                                           'actif': True,
                                                           'indice': "{:02d}".format(indice + 1)})
        return True

