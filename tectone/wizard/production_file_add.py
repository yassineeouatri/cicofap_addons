# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
from odoo import api, models, fields
from datetime import datetime


class production_document_file_add(models.Model):
    _name = 'production.document.file.add'

    document_id = fields.Many2one('production.document', 'Document', required=True, ondelete='cascade')
    filename = fields.Char("Nom du fichier", size=256)
    file = fields.Binary("Fichier")

    def action_done(self):
        document_obj = self.env['production.document'].search([('id', '=', self.document_id.id)],order='indice desc', limit=1)
        if document_obj:
            document_obj.write({'file': self.file, 'filename': self.filename})

            self.env['production.document.file'].create({'document_id': self.document_id.id,
                                                         'date': datetime.today(),
                                                         'file': self.file,
                                                         'filename': self.filename})
        return True

