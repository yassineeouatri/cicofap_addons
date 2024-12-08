from odoo import models, fields, api, _
from odoo.exceptions import UserError


class ProductionDocumentSend(models.TransientModel):
    _name = "production.document.send"
    _description = "Send multiple documents"

    manager_id = fields.Many2one('production.employee', 'Responsable', required=True)

    def send_documents(self):
        domain = [('id', 'in', self._context.get('active_ids', [])), ('state', '=', 'draft')]
        documents = self.env['production.document'].search(domain)
        if not documents:
            raise UserError(_('Merci de sélectionner un document'))
        for document in documents:
            document.action_ready(self.manager_id.id)
        return {'type': 'ir.actions.act_window_close'}

    def send_document(self):
        domain = [('id', '=', self._context.get('active_id')), ('state', '=', 'draft')]
        document = self.env['production.document'].search(domain)[0]
        document.action_ready(self.manager_id.id)
        return {'type': 'ir.actions.act_window_close'}

