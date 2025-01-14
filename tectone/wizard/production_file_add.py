# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
import os
from datetime import datetime
from odoo import api, models, fields
from odoo.exceptions import UserError


class production_document_file_add(models.Model):
    _name = 'production.document.file.add'

    document_id = fields.Many2one('production.document', 'Document', required=True, ondelete='cascade')
    filename = fields.Char("Nom du fichier", size=256)
    file = fields.Binary("Fichier")

    def action_done(self):
        document_obj = self.env['production.document'].search([('id', '=', self.document_id.id)],order='indice desc', limit=1)
        if document_obj:
            document_name = os.path.splitext(self.filename)[0]
            document_titre = f'-{self.document_id.name}' if self.document_id.name else ''
            document_code = f'{self.document_id.full_name}{document_titre}'
            if document_name != document_code:
                raise UserError(f"La nom du document ajouté <{document_name}> doit correspondre à la codification actuelle du document <{document_code}>!")

            document_obj.write({'file': self.file, 'filename': self.filename})
            self.env['production.document.file'].create({'document_id': self.document_id.id,
                                                         'date': datetime.today(),
                                                         'file': self.file,
                                                         'filename': self.filename})
        return True

