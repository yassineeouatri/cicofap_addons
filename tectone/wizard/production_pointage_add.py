# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
from odoo import api, models, fields
from datetime import datetime


class production_pointage_add(models.Model):
    _name = 'production.pointage.add'

    pointage_id = fields.Many2one('production.pointage', 'Pointage', required=True, ondelete='cascade')
    affaire_id = fields.Many2one('production.affaire', 'Affaire', required=True)
    type = fields.Selection([('meeting', 'Réunion'), ('document', 'Document'), ('research', 'Recherche'),
                             ('modelisation_cao', 'Modélisation CAO'), ('modelisation_calcul', 'Modélisation Calcul'),
                             ('stand', 'Stand-By'), ('other', 'Autre')], 'Type',
                            required=True)
    reunion_id = fields.Many2one('production.reunion', 'Réunion')
    document_id = fields.Many2one('production.document', 'Document')
    document_ids = fields.Many2many('production.document', 'rel_pointage_document', 'document_id', 'pointage_id', 'Documents')
    task = fields.Char('Tâche')
    nb_hour = fields.Selection([('0', '0h'),
                                ('0.5', '1/2h'),
                                ('1', '1h'), ('1.5', '1.5h'),
                                ('2', '2h'), ('2.5', '2.5h'),
                                ('3', '3h'), ('3.5', '3.5h'),
                                ('4', '4h'), ('4.5', '4.5h'),
                                ('5', '5h'), ('5.5', '5.5h'),
                                ('6', '6h'), ('6.5', '6.5h'),
                                ('7', '7h'), ('7.5', '7.5h'),
                                ('8', '8h'), ('8.5', '8.5h')], "Nb d'heure", default='0')
    hour = fields.Float("Nb d'heure")

    @api.onchange('nb_hour')
    def _onchange_nb_hour(self):
        self.hour = float(self.nb_hour)

    def action_done(self):
        values = {
            'pointage_id': self.pointage_id.id,
            'affaire_id': self.affaire_id.id,
            'type': self.type,
            'task': self.task,
            'nb_hour': '0',
            'hour': 0
                  }
        if self.document_ids:
            for document in self.document_ids:
                values['document_id'] = document.id
                self.env['production.pointage.line'].create(values)
        elif self.reunion_id:
            values['reunion_id'] = self.reunion_id.id
            values['nb_hour'] = self.nb_hour
            values['hour'] = self.hour
            self.env['production.pointage.line'].create(values)
        else:
            values['nb_hour'] = self.nb_hour
            values['hour'] = self.hour
            self.env['production.pointage.line'].create(values)
        return True

