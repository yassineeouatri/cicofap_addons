# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
import os
import time
import base64
import openpyxl
from odoo import api, models, fields, _, SUPERUSER_ID
from odoo.exceptions import AccessError, ValidationError, UserError
from datetime import datetime


SERVER_ADRESS = 'http://192.168.0.35'
#SERVER_ADRESS = 'http://localhost:8069'
EMAIL_FROM = 'tectonegroup@outlook.com'
LOCAL_DIRECTORY = "C://Program Files//Odoo15//server//odoo//addons//web//static//reports"
LOCAL_REPORTS_DIRECTORY = "/web/static/reports/"
LOCAL_DIRECTORY = "C://Users//Yassine//PycharmProjects//cicofap//Scripts//odoo//addons//web//static//reporting//"
LOCAL_REPORTS_DIRECTORY = "web/static/reporting/"

class production_job(models.Model):
    _name = 'production.job'
    _description = 'Postes'

    name = fields.Char('Poste', required=True)

class production_employee(models.Model):
    _name = 'production.employee'

    name = fields.Char('Nom et Prénom', required=True)
    email = fields.Char('Email')
    job_id = fields.Many2one('production.job', 'Poste')
    is_manager = fields.Boolean('Est un responsable?')
    user_id = fields.Many2one('res.users', 'Utilisateur')

class production_emetteur(models.Model):
    _name = 'production.emetteur'
    _rec_name = 'display_name'

    display_name = fields.Char(compute='_compute_display_name')
    name = fields.Char('Emetteur', required=True)
    description = fields.Char('Description')

    @api.depends('name', 'description')
    def _compute_display_name(self):
        for record in self:
            if record.description:
                record.display_name = _("%s - %s", record.name, record.description)
            else:
                record.display_name = _("%s", record.name)


class production_scope(models.Model):
    _name = 'production.scope'
    _order = 'name'

    name = fields.Char('Code', required=True)
    designation = fields.Char('Désignation')

class production_ouvrage(models.Model):
    _name = 'production.ouvrage'
    _rec_name = 'display_name'

    display_name = fields.Char(compute='_compute_display_name')
    name = fields.Char('Ouvrage', required=True)
    description = fields.Char('Desription')

    @api.depends('name', 'description')
    def _compute_display_name(self):
        for record in self:
            if record.description:
                record.display_name = _("%s - %s", record.name, record.description)
            else:
                record.display_name = _("%s", record.name)

class production_phase(models.Model):
    _name = 'production.phase'
    _rec_name = 'display_name'

    display_name = fields.Char(compute='_compute_display_name')
    name = fields.Char('Phase', required=True)
    description = fields.Char('Desription')

    @api.depends('name', 'description')
    def _compute_display_name(self):
        for record in self:
            if record.description:
                record.display_name = _("%s - %s", record.name, record.description)
            else:
                record.display_name = _("%s", record.name)

class production_reunion(models.Model):
    _name = 'production.reunion'

    name = fields.Char('Réunion', required=True)
    sequence = fields.Integer('Sequence', default=0)

class production_document_type(models.Model):
    _name = 'production.document.type'
    _rec_name = 'display_name'
    _order = 'name'

    display_name = fields.Char(compute='_compute_display_name')
    name = fields.Char('Nom', required=True)
    description = fields.Char('Description')
    type = fields.Selection([('note', 'Note'), ('echange', 'Echange'), ('plan', 'Plan')], 'Type', required=True)
    sequence = fields.Integer('Sequence', default=0)

    @api.depends('name', 'description')
    def _compute_display_name(self):
        for record in self:
            if record.description:
                record.display_name = _("%s - %s", record.name, record.description)
            else:
                record.display_name = _("%s", record.name)

class production_document(models.Model):
    _name = 'production.document'
    _description = 'Document'
    _inherit = ['mail.thread']
    _rec_name = 'full_name'
    _order = 'date desc'
    _mail_post_access = 'read'  # Specifies the access level required to post messages

    def _default_employee(self):
        employee_obj = self.env['production.employee'].search([('user_id', '=', self.env.user.id)])
        if employee_obj:
            return employee_obj.id
        return False

    def _default_emetteur_id(self):
        emetteur_obj = self.env['production.emetteur'].search([('name', '=', 'TCT')])
        return emetteur_obj.id

    full_name = fields.Char(string='Code', readonly=True,
                       states={'draft': [('readonly', False)], 'wait': [('readonly', False)]}, compute='_compute_full_name', store=True)
    name = fields.Char('Titre du document', readonly=True,
                       states={'draft': [('readonly', False)], 'wait': [('readonly', False)]})
    file = fields.Binary('Fichier', readonly=True)
    filename = fields.Char('Nom du fichier')
    numero = fields.Char('N° Document', default='001', required=True,  readonly=True, states={'draft': [('readonly', False)], 'wait': [('readonly', False)]}, size=3)
    indice = fields.Char('Indice', default='00', required=True, readonly=True, sie=2)
    date = fields.Date('Date création', default=datetime.today(), required=True, readonly=True)
    employee_id = fields.Many2one('production.employee', 'Nom et Prénom', default=_default_employee, required=True, readonly=True)
    affaire_id = fields.Many2one('production.affaire', 'Affaire', required=True, readonly=True,
                                 states={'draft': [('readonly', False)], 'wait': [('readonly', False)]})
    phase_id = fields.Many2one('production.phase', 'Phase', readonly=True,
                              states={'draft': [('readonly', False)], 'wait': [('readonly', False)]},domain="[('id', 'in', available_phase_ids)]")
    available_phase_ids = fields.Many2many('production.phase', compute='_compute_available_phase_ids', store=False)
    type_id = fields.Many2one('production.document.type', 'Identifiant Document', readonly=True,
                              states={'draft': [('readonly', False)], 'wait': [('readonly', False)]})
    scope_id = fields.Many2one('production.scope', 'Scope',  readonly=True,
                                states={'draft': [('readonly', False)], 'wait': [('readonly', False)]})
    zone_id = fields.Many2one('production.zone', 'Zone', readonly=True,
                              states={'draft': [('readonly', False)], 'wait': [('readonly', False)]})
    ouvrage_id = fields.Many2one('production.ouvrage', "Ouvrage", readonly=True,
                              states={'draft': [('readonly', False)], 'wait': [('readonly', False)]})
    emetteur_id = fields.Many2one('production.emetteur', 'Emetteur', required=True, readonly=True,
                                  states={'draft': [('readonly', False)], 'wait': [('readonly', False)]},
                                  default=_default_emetteur_id)
    bordereau_id = fields.Many2one('production.bordereau', 'Bordereau')
    indice_ids = fields.One2many('production.document.indice', 'document_id', 'Indices', ondelete='cascade')
    file_ids = fields.One2many('production.document.file', 'document_id', 'Fichiers', ondelete='cascade')
    date_bordereau = fields.Date('Date bordereau', readonly=True)
    date_crt = fields.Date('Date envoi CRT', readonly=True)
    date_client = fields.Date('Date envoi Client', readonly=True)
    note_ids = fields.One2many('production.document.note', 'document_id', 'Notes', readonly=True)
    # visible and required fields
    zone_id_required = fields.Boolean('Zone required', default=True)
    zone_id_visible = fields.Boolean('Zone Visible', default=True)
    phase_id_visible = fields.Boolean('Phase Visible', default=True)
    scope_id_required = fields.Boolean('Scope required', default=True)
    scope_id_visible = fields.Boolean('Scope Visible', default=True)
    type_id_required = fields.Boolean('Type required', default=True)
    type_id_visible = fields.Boolean('Type Visible', default=True)
    ouvrage_id_required = fields.Boolean('Ouvrage required', default=True)
    ouvrage_id_visible = fields.Boolean('Ouvrage Visible', default=True)

    state = fields.Selection(
        [('draft', 'Draft'), ('ready', 'Ready'), ('sent_crt', 'Envoyé à la CRT'), ('return', 'Return'), ('wait', 'Attente'),
         ('sent_client', 'Envoyé au client')], readonly=True, default='draft', copy=False, string="Etat", track_visibility='onchange')

    _sql_constraints = [('uniq_document', 'unique(full_name)', "Chaque document a un code unique!")]

    @api.depends('affaire_id')
    def _compute_available_phase_ids(self):
        for record in self:
            if record.affaire_id:
                record.available_phase_ids = record.affaire_id.phase_ids
            else:
                record.available_phase_ids = []

    @api.onchange('affaire_id')
    def _onchange_affaire_id(self):
        if self.affaire_id:
            self.available_phase_ids = self.affaire_id.phase_ids
        else:
            self.available_phase_ids = self.env['production.phase'].browse()
        self.zone_id = None
        self.phase_id = None
        self.type_id = None
        self.ouvrage_id = None
        self.zone_id_visible = self.affaire_id.zone_id_visible
        self.phase_id_visible = self.affaire_id.phase_id_visible
        self.type_id_visible = self.affaire_id.type_id_visible
        self.ouvrage_id_visible = self.affaire_id.ouvrage_id_visible
        self.numero = '001'

    @api.onchange('zone_id')
    def _onchange_zone_id(self):
        numero = None
        zone = self.env['production.zone'].search([('id', '=', self.zone_id.id)], limit=1)
        if zone:
            self._cr.execute("select numero from production_document where zone_id="+str(zone.id)+" order by numero desc limit 1")
            for res in self._cr.fetchall():
                if res:
                    numero = int(res[0]) + 1
        if not numero:
            numero = zone.from_indice
        self.numero = "{:03d}".format(numero)

    @api.depends('emetteur_id', 'zone_id', 'phase_id', 'ouvrage_id', 'type_id', 'numero', 'indice')
    def _compute_full_name(self):
        for record in self:
            full_name = ''
            if record.emetteur_id:
                full_name +=  f"{record.emetteur_id.name}"
            if record.zone_id:
                full_name += f"-{record.zone_id.name}"
            if record.phase_id:
                full_name += f"-{record.phase_id.name}"
            if record.ouvrage_id:
                full_name += f"-{record.ouvrage_id.name}"
            if record.type_id:
                full_name += f"-{record.type_id.name}"
            if record.numero:
                full_name += f"-{record.numero}"
            if record.indice:
                full_name += f"-{record.indice}"
            record.full_name = full_name

    @api.model
    def create(self, values):
        numero = values['numero']
        zone_id = values['zone_id']

        if not numero.isnumeric():
            raise UserError("La valeur '{}' saisie pour le champs numéro doit être numérique!".format(numero))
        elif int(numero) == 0 :
            raise UserError("La valeur '{}' saisie pour le champs numéro doit être supérieur à 000!".format(numero))
        elif len(numero) != 3:
            raise UserError("La valeur '{}' saisie pour le champs numéro doit contenir 3 chiffres!".format(numero))
        else:
            if zone_id:
                zone = self.env['production.zone'].search([('id', '=', zone_id)], limit=1)
                if zone.need_plage and (int(numero) < int(zone.from_indice) or int(numero) > int(zone.to_indice)):
                    raise UserError("La valeur '{}' saisie pour le champs numéro doit être dans la range[{}, {}]!".format(numero, zone.from_indice, zone.to_indice))

        document = super(production_document, self).create(values)
        # Post comment on a model
        # self.env.user.notify_info("Document crée avec succès")
        """document.message_post(
            body="Hello everybody",
            message_type="notification",  # You can also use "comment"
            subtype="mail.mt_comment",
            partner_ids=[self.env.user.partner_id.id]  # Add the partner_id to send the message to a specific user
        )"""
        # Post a message to the specified user
        # document.send_message("cc", self.env.user.partner_id.id)
        #document.message_post(subject="subject", body="body", partner_ids=[self.env.user.partner_id.id])
        """# create indice
        self.env['production.document.indice'].create({'document_id': document.id,
                                                       'nature': 'Première diffusion',
                                                       'date': datetime.today(),
                                                       'actif': True,
                                                       'indice': "{:02d}".format(0)})"""
        return document

    def write(self, values):
        numero = values.get('numero', None)
        if numero:
            if not numero.isnumeric():
                raise UserError("La valeur '{}' saisie pour le champs numéro doit être numérique!".format(numero))
            elif int(numero) == 0:
                raise UserError("La valeur '{}' saisie pour le champs numéro doit être supérieur à 000!".format(numero))
            elif len(numero) != 3:
                raise UserError("La valeur '{}' saisie pour le champs numéro doit contenir 3 chiffres!".format(numero))
            else:
                if self.zone_id:
                    zone = self.env['production.zone'].search([('id', '=', self.zone_id.id)], limit=1)
                    if zone.need_plage and (int(numero) < int(zone.from_indice) or int(numero) > int(zone.to_indice)):
                        raise UserError(
                            "La valeur '{}' saisie pour le champs numéro doit être dans la range[{}, {}]!".format(
                                numero, zone.from_indice, zone.to_indice))

        return super(production_document, self).write(values)

    @api.model
    def default_get(self, vals):
        # company_id is added so that we are sure to fetch a default value from it to use in repartition lines, below
        rslt = super(production_document, self).default_get(vals)
        rslt['indice_ids'] = [
            (0, 0, {'nature': 'Première diffusion', 'date': datetime.today(), 'actif': True, 'indice': "{:02d}".format(1)})
        ]
        return rslt

    def unlink(self):
        """for record in self:
            if record.state not in ('draft'):
                raise UserError("Vous ne pouvez pas supprimer un document qui n'est pas à l'état de brouillon!")"""
        return super(production_document, self).unlink()

    def send_message(self, bordereau_obj, partner_id):
        notification_ids = []
        notification_ids.append((0, 0, {
            'res_partner_id': partner_id,
            'notification_type': 'inbox'}))
        bordereau_obj.message_post(body="Nouveau bordereau", message_type='notification',
                          subtype_xmlid='mail.mt_comment', author_id=self.env.user.partner_id.id,
                          notification_ids=notification_ids)

    def send_mail(self, bordereau_obj):
        mail_pool = self.env['mail.mail']
        values = {}
        emails = [bordereau_obj.manager_id.email]
        body1 = "<ul>"
        attachment_ids = []
        body1 += "</ul>"
        action = self.env['ir.actions.act_window'].search([('res_model', '=', 'production.bordereau'), ('name', '=', "Bordereaux d'envoi")], limit=1)
        action_id = action.id
        menu = self.env['ir.ui.menu'].search([('action', '=', f'ir.actions.act_window,{action_id}')], limit=1)
        menu_id = menu.id
        body = """<div style="margin: 0px; padding: 0px;">
                    <div style="margin: 0px; padding: 0px; font-size: 13px;">
                        Bonjour,
                        <br /><br />
                        Vous recevez cet email suite à un nouvel bordereau crée de la part <strong>""" + bordereau_obj.employee_id.name + """</strong>.
                        <br /><br />
                        Vous pouvez accéder au bordereau en cliquant sur le lien ci-dessous :
                        <a href={}/web#id={}&cids=1&menu_id={}&action={}&model=production.bordereau&view_type=form>Lien</a>
                        <br /><br />
                        Cordialement,
                    </p>
                </div>""".format(SERVER_ADRESS, bordereau_obj.id, menu_id, action_id)
        values.update({'subject': bordereau_obj.affaire_id.full_name + ' - Nouveau bordereau'})
        values.update({'email_from': EMAIL_FROM})
        values.update({'email_to': ','.join(emails)})
        values.update({'body_html': body})
        if attachment_ids:
            values.update({'attachment_ids': [(6, 0, attachment_ids)]})
        # values.update({'res_id': 'obj.id'})  # [optional] here is the record id, where you want to post that email after sending
        values.update({'model': 'production.bordereau'})  # [optional] here is the object(like 'project.project')  to whose record id you want to post that email after sending
        msg_id = mail_pool.create(values)
        # And then call send function of the mail.mail,
        if msg_id:
            mail_pool.send([msg_id])
        return  True

    def action_ready(self, manager_id):
        # create bordereau record
        order = 0
        employee_obj = self.env['production.employee'].search([('id', '=', manager_id)])
        bordereau_obj = self.env['production.bordereau'].search([('affaire_id', '=', self.affaire_id.id),
                                                                 ('employee_id', '=', self.employee_id.id),
                                                                 ('state', '=', 'draft')])

        if not bordereau_obj:
            bordereau_obj = self.env['production.bordereau'].create({'affaire_id': self.affaire_id.id,
                                                                     'employee_id': self.employee_id.id,
                                                                     'manager_id': manager_id,
                                                                     'date': datetime.today()})
            if employee_obj:
                if employee_obj.user_id:
                    # send web notification to manager
                    # employee_obj.user_id.notify_info("Nouveau bordereau crée", self.affaire_id.name)

                    # send notification to manager
                    self.send_message(bordereau_obj, employee_obj.user_id.partner_id.id)

                    # send email
                    # self.send_mail(bordereau_obj)

        # self.env.user.notify_info("Le document {} a été bien ajouté au bordereau".format(self.full_name))

        # create bordereau line record
        self.env['production.bordereau.line'].create({'bordereau_id': bordereau_obj.id,
                                                      'document_id': self.id})
        for indice_obj in self.indice_ids:
            indice_obj.write({'state': 'ready'})
        return self.write({'state': 'ready', 'bordereau_id': bordereau_obj.id, 'date_bordereau': datetime.today()})

    def action_wait(self):
        bordereau_line_obj = self.env['production.bordereau.line'].search([('document_id', '=', self.id)], order='id desc', limit=1)
        if bordereau_line_obj:
            state = bordereau_line_obj.bordereau_id.state
            if state == 'sent_crt':
                bordereau_line_obj.write({'state': 'sent_crt'})
                self.write({'state': 'sent_crt'})
            """else:
                return {
                    "type": "ir.actions.act_window",
                    "res_model": "production.document.send",
                    "view_mode": "form",
                    "view_type": "form",
                    "views": [
                        (
                            self.env.ref("tectone.production_document_send_view").id,
                            "form",
                        )
                    ],
                    "target": "new",
                    "flags": {"form": {"action_buttons": True}},
                }"""
        return True

    def action_return(self):
        bordereau_line_obj = self.env['production.bordereau.line'].search([('document_id', '=', self.id)],
                                                                          order='id desc', limit=1)
        if bordereau_line_obj:
            state = bordereau_line_obj.bordereau_id.state
            if state == 'sent_crt':
                bordereau_line_obj.write({'state': 'sent_crt'})
                self.write({'state': 'sent_crt'})
        return True

    def action_draft(self):
        order = 0
        bordereau_obj = self.env['production.bordereau'].search([('affaire_id', '=', self.affaire_id.id),
                                                                 ('employee_id', '=', self.employee_id.id),
                                                                 ('state', '=', 'draft')])
        if bordereau_obj:
            bordereau_line_obj = self.env['production.bordereau.line'].search([('bordereau_id', '=', bordereau_obj.id),
                                                                               ('document_id', '=', self.id)])
            if bordereau_line_obj:
                for line in bordereau_line_obj:
                    line.unlink()
        for indice_obj in self.indice_ids:
            indice_obj.write({'state': 'draft'})
        return self.write({'state': 'draft', 'bordereau_id': None})

    def action_add_indices(self):
        return {
            "type": "ir.actions.act_window",
            "res_model": "production.document.indice.add",
            "view_mode": "form",
            "view_type": "form",
            "views": [
                (
                    self.env.ref("tectone.production_document_indice_create_view_form").id,
                    "form",
                )
            ],
            "context": {"default_document_id": self.id},
            "target": "new",
            "flags": {"form": {"action_buttons": True}},
        }

    def action_add_files(self):
        return {
            "type": "ir.actions.act_window",
            "res_model": "production.document.file.add",
            "view_mode": "form",
            "view_type": "form",
            "views": [
                (
                    self.env.ref("tectone.production_document_file_create_view_form").id,
                    "form",
                )
            ],
            "context": {"default_document_id": self.id},
            "target": "new",
            "flags": {"form": {"action_buttons": True}},
        }

    def action_send(self):
        # Contrôle d'existence d'un fichier attaché au document
        if not self.file:
            raise ValidationError(
                _("Vous ne pouvez pas ajouter ce document au bordereau tant qu'aucun plan n'est attaché.")
            )

        bordereau_obj = self.env['production.bordereau'].search([('affaire_id', '=', self.affaire_id.id),
                                                                 ('employee_id', '=', self.employee_id.id),
                                                                 ('state', '=', 'draft')])
        if bordereau_obj:
            # Send notification
            #self.env.user.notify_info("Le document {} a été bien ajouté au bordereau".format(self.full_name))
            if bordereau_obj.manager_id:
                if bordereau_obj.manager_id.user_id:
                    # send web notification to manager
                    # bordereau_obj.manager_id.user_id.notify_info( "Un nouveau document {} a été ajouté au borderau {}".format(self.name, bordereau_obj.name))

                    # send notification to manager
                    self.send_message(bordereau_obj, bordereau_obj.manager_id.user_id.partner_id.id)
            # create bordereau line record
            self.env['production.bordereau.line'].create({'bordereau_id': bordereau_obj.id,
                                                          'document_id': self.id})
            for indice_obj in self.indice_ids:
                indice_obj.write({'state': 'ready'})
            return self.write({'state': 'ready', 'bordereau_id': bordereau_obj.id, 'date_bordereau': datetime.today()})
        else:
            return {
                "type": "ir.actions.act_window",
                "res_model": "production.document.send",
                "view_mode": "form",
                "view_type": "form",
                "views": [
                    (
                        self.env.ref("tectone.production_document_send_view").id,
                        "form",
                    )
                ],
                "target": "new",
                "flags": {"form": {"action_buttons": True}},
            }

class production_document_indice(models.Model):
    _name = 'production.document.indice'

    document_id = fields.Many2one('production.document', 'Document', required=True, ondelete='cascade')
    date = fields.Date('Date', default=datetime.today(), required=True, readonly=True)
    indice = fields.Char('Indice', required=True, size=2, readonly=True)
    nature = fields.Char('Description', required=True)
    actif = fields.Boolean('Actif', default=False, readonly=True)
    is_send = fields.Boolean('Envoyé à CRT', default=False)
    date_crt = fields.Date('Date envoi CRT')
    date_client = fields.Date('Date envoi Client')
    state = fields.Selection(
        [('draft', 'Draft'), ('ready', 'ready'), ('sent', 'Sent')], readonly=True, default='draft', copy=False,
        string="Etat")

    def unlink(self):
        records_to_delete = []
        for record in self:
            records_to_delete.append(record.id)
        indice = 0
        document_indice_obj = self.env['production.document.indice'].search([('document_id', '=', self.document_id.id),
                                                                             ('id', 'not in', records_to_delete)], order='indice desc', limit=1)
        if document_indice_obj:
            indice = int(document_indice_obj.indice)

        if self.document_id.state == 'draft':
            self.document_id.write({'indice': "{:02d}".format(indice)})

            document_indice_ids = self.env['production.document.indice'].search(
                [('document_id', '=', self.document_id.id)])
            for record in document_indice_ids:
                record.write({'actif': False})

            document_indice_ids = self.env['production.document.indice'].search(
                [('document_id', '=', self.document_id.id), ('indice', '=', "{:02d}".format(indice))])
            for record in document_indice_ids:
                record.write({'actif': True})
            return super(production_document_indice, self).unlink()
        return True

class production_document_file(models.Model):
    _name = 'production.document.file'
    _order = 'date desc'

    document_id = fields.Many2one('production.document', 'Document', required=True, ondelete='cascade')
    date = fields.Date('Date', default=datetime.today(), required=True, readonly=True)
    file = fields.Binary('Fichier', required=True, attachment=False, readonly=True)
    filename = fields.Char('File Name', required=True, readonly=True)

    def unlink(self):
        records_to_delete = []
        for record in self:
            records_to_delete.append(record.id)
        file = None
        filename = None
        document_file_obj = self.env['production.document.file'].search([('document_id', '=', self.document_id.id),
                                                                             ('id', 'not in', records_to_delete)],
                                                                            order='id desc', limit=1)
        if document_file_obj:
            file = document_file_obj.file
            filename = document_file_obj.filename

        if self.document_id.state == 'draft':
            self.document_id.write({'file': file, 'filename': filename})
            return super(production_document_file, self).unlink()
        return True

class production_document_note(models.Model):
    _name = 'production.document.note'
    _order = 'date desc'

    document_id = fields.Many2one('production.document', 'Document', required=True, ondelete='cascade')
    date = fields.Date('Date', default=datetime.today())
    user_id = fields.Many2one('res.users', 'Crée par')
    note = fields.Text('Remarque')

class production_bordereau(models.Model):
    _name = 'production.bordereau'
    _description = "Bordereau"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'date desc'
    _mail_post_access = 'read'  # Specifies the access level required to post messages

    name = fields.Char(string="Bordereau", default="*", readonly=True, help="Nom du bordereau")
    date = fields.Date('Date de création', default=datetime.today(), required=True, readonly=True)
    date_crt = fields.Date("Date envoi CRT", readonly=True)
    date_client = fields.Date("Date envoi Client", readonly=True)
    order = fields.Char('Numéro')
    zones = fields.Char('Zones')
    affaire_id = fields.Many2one('production.affaire', 'Affaire', required=True, readonly=True)
    employee_id = fields.Many2one('production.employee', 'Employé', required=True, readonly=True)
    manager_id = fields.Many2one('production.employee', 'Responsable', required=True, readonly=True)
    line_ids = fields.One2many('production.bordereau.line', 'bordereau_id', 'lines', readonly=True)
    state = fields.Selection([('draft', 'Draft'), ('sent_crt', 'Envoyé CRT'), ('sent_client', 'Envoyé Client')],
                             readonly=True, default='draft', copy=False,
                             string="Etat", track_visibility='onchange')

    def get_emails_validation(self, emails = []):
        self._cr.execute("""select email,job.name from production_employee emp
                            inner join production_job job on job.id=emp.job_id
                            where job.name like 'CRT'""")
        for res in self._cr.fetchall():
            emails.append(res[0])
        self._cr.execute("""select email from production_employee where id=""" + str(self.manager_id.id))
        for res in self._cr.fetchall():
            emails.append(res[0])
        self._cr.execute("""select email from production_employee where id=""" + str(self.employee_id.id))
        for res in self._cr.fetchall():
            emails.append(res[0])
        emails = list(set(emails))
        emails = ','.join(emails)
        return  emails

    def get_emails(self, emails = []):
        # Get Admin emails
        self._cr.execute("""select email from production_employee emp
                            inner join production_job job on job.id=emp.job_id
                            where job.name like 'Adm%'""")
        for res in self._cr.fetchall():
            emails.append(res[0])
        # Get CRT emails
        self._cr.execute("""select email from production_employee emp
                            inner join production_job job on job.id=emp.job_id
                            where job.name like 'CRT'""")
        for res in self._cr.fetchall():
            emails.append(res[0])
        # Get Ingénieurs emails
        self._cr.execute("""select email from production_employee emp
                            inner join production_job job on job.id=emp.job_id
                            where job.name like 'Ing%'""")
        for res in self._cr.fetchall():
            emails.append(res[0])
        self._cr.execute("""select email from production_employee where id=""" + str(self.manager_id.id))
        for res in self._cr.fetchall():
            emails.append(res[0])
        self._cr.execute("""select email from production_employee where id=""" + str(self.employee_id.id))
        for res in self._cr.fetchall():
            emails.append(res[0])
        emails = list(set(emails))
        emails = ','.join(emails)
        return  emails

    def action_sent_crt(self):
        for line in self.line_ids:
            line.write({'state': 'sent_crt'})
            #####################
            line_obj = self.env['production.document'].search([('id', '=', line.document_id.id)])
            if line_obj:
                line_obj.write({'state': 'sent_crt', 'date_crt': datetime.today()})
            ####################
            lines_obj = self.env['production.document.indice'].search([('document_id', '=', line.document_id.id),
                                                                       ('is_send', '=', False)])
            if lines_obj:
                for record in lines_obj:
                    record.write({'is_send': True, 'date_crt': datetime.today()})

        mail_pool = self.env['mail.mail']
        values = {}
        emails = self.get_emails_validation() # Récupère les e-mails des destinataires

        body1 = "<ul>"
        attachment_ids = []
        attachment_ids.append(self.generate_bordereau_attachement())
        # Attach documents files
        for rec in self.line_ids:
            body1 += f"<li>{rec.document_id.full_name}</li>"
            if rec.document_id.full_name:
                attach_data = {
                    'name': rec.document_id.filename,
                    'datas': rec.document_id.file,
                    'res_model': 'production.document',
                    'res_id': rec.document_id.id,
                    "type": "binary",
                }
                attach_id = self.env ['ir.attachment'].create(attach_data)
                attachment_ids.append(attach_id.id)
        body1 += "</ul>"

        # Récupération des identifiants d'action et de menu
        action = self.env['ir.actions.act_window'].search([('res_model', '=', 'production.bordereau'), ('name', '=', "Bordereaux d'envoi")], limit=1)
        action_id = action.id
        menu = self.env['ir.ui.menu'].search([('action', '=', f'ir.actions.act_window,{action_id}')], limit=1)
        menu_id = menu.id

        # Construction du corps de l'email
        body = f"""
        <div style="margin: 0px; padding: 0px;">
            <div style="margin: 0px; padding: 0px; font-size: 13px;">
                Bonjour,<br /><br />
                Vous recevez cet email suite à une demande de validation de la part <strong>{self.employee_id.name}</strong>.
                <br /><br />
                Le borderau contient la liste des documents suivants:
                {body1}
                <br /><br />
                Veuillez prendre quelques instants pour examiner le bordereau et confirmer sa validité. 
                Vous pouvez accéder au bordereau en cliquant sur le lien ci-dessous :
                <a href="{SERVER_ADRESS}/web#id={self.id}&cids=1&menu_id={menu_id}&action={action_id}&model=production.bordereau&view_type=form">Lien</a>
                <br /><br />
                Cordialement,
            </div>
        </div>
        """
        # Préparation des valeurs de l'email
        values.update({
            'subject': f"{self.affaire_id.full_name} - Bordereau à valider",
            'email_from': EMAIL_FROM,  # Assurez-vous que cet email est correctement configuré
            'email_to': emails,  # Liste des destinataires
            'body_html': body,
            'model': 'production.bordereau',  # Lié au modèle `production.bordereau`
        })

        if attachment_ids:
            values.update({'attachment_ids': [(6, 0, attachment_ids)]})
        #values.update({'res_id': 'obj.id'})  # [optional] here is the record id, where you want to post that email after sending
        values.update({'model': 'production.bordereau'})  # [optional] here is the object(like 'project.project')  to whose record id you want to post that email after sending
        msg_id = mail_pool.create(values)

        # And then call send function of the mail.mail,
        if msg_id:
            mail_pool.send([msg_id])
        return self.write({'state': 'sent_crt', 'date_crt': datetime.today()})

    def action_sent_client(self):
        line_ids = self.env['production.bordereau.line'].search([('bordereau_id', '=', self.id), ('state', '=', 'sent_crt')])
        if line_ids:
            raise ValidationError(_("Vous ne pouvez pas envoyer ce bordereau tant qu'il y a un document non encore validé"))
        #############################################
        line_ids = self.env['production.bordereau.line'].search([('bordereau_id', '=', self.id), ('state', '=', 'draft')])
        if line_ids:
            raise ValidationError(_("Vous ne pouvez pas envoyer ce bordereau tant qu'il y a un document en état brouillon"))
        #################################################
        line_ids = self.env['production.bordereau.line'].search([('bordereau_id', '=', self.id), ('state', '=', 'validate')])
        for line in line_ids:
            document_obj = self.env['production.document'].search([('id', '=', line.document_id.id)])
            if document_obj:
                document_obj.write({'state': 'sent_client', 'date_client': datetime.today()})
            ####################
            lines_obj = self.env['production.document.indice'].search([('document_id', '=', line.document_id.id), ('actif', '=', False)])
            if lines_obj:
                for record in lines_obj:
                    record.write({'is_send': True, 'date_client': datetime.today()})
        ###################update order and name fields value######################################
        line_obj = self.env['production.bordereau'].search([('affaire_id','=', self.affaire_id.id), ('state', '=', 'sent_client')], order='order desc', limit=1)
        if line_obj:
            order = line_obj.order
            if not order:
                order = 0
            else:
                order = int(order)
        else:
            order = 0
        order = "{:03d}".format(order + 1)
        name = "BE-{}".format(order)
        # Send email
        mail_pool = self.env['mail.mail']
        emails = []
        for rec in self.affaire_id.email_ids:
            if rec.name:
                emails.append(rec.name)
        emails = self.get_emails(emails)
        attachments = []
        attachments.append(self.generate_bordereau_attachement(order=order, send_crt=Tr))
        body1 = "<table style='border-collapse: collapse;'>"
        for rec in self.line_ids:
            if rec.state == 'validate':
                emetteur = rec.document_id.emetteur_id.name if rec.document_id.emetteur_id else ''
                phase = rec.document_id.phase_id.name if rec.document_id.phase_id else ''
                zone = rec.document_id.zone_id.name if rec.document_id.zone_id else ''
                ouvrage = rec.document_id.ouvrage_id.name if rec.document_id.ouvrage_id else ''
                identifiant = rec.document_id.type_id.name if rec.document_id.type_id else ''
                name = rec.document_id.name if rec.document_id.name else ''

                body1 += "<tr>" \
                         "<td style='text-align: center;border: 1px solid;padding: 10px;'>" + str(emetteur) + "</td>" + \
                         "<td style='text-align: center;border: 1px solid;padding: 10px;'>" + str(zone) + "</td>" + \
                         "<td style='text-align: center;border: 1px solid;padding: 10px;'>" + str(phase) + "</td>" + \
                         "<td style='text-align: center;border: 1px solid;padding: 10px;'>" + str(ouvrage) + "</td>" + \
                         "<td style='text-align: center;border: 1px solid;padding: 10px;'>" + str(identifiant) + "</td>" + \
                         "<td style='text-align: center;border: 1px solid;padding: 10px;'>" + str(rec.document_id.numero) + "</td>" + \
                         "<td style='text-align: center;border: 1px solid;padding: 10px;'>" + str(rec.document_id.indice) + "</td>" + \
                         "</tr>"
        body1 += "</table>"
        body = """<div style="margin: 0px; padding: 0px; font-size: 13px;">
                            Bonjour,
                            <br /><br />
                            Veuillez trouver ci-joint le bordereau d'envoi BE TECTONE N°"""+str(order)+""" relatifs aux documents:
                            <br /><br />
                            """ + body1 + """
                            <br />
                            Nous vous souhaitons bonne réception de ces éléments.
                            <br /><br />
                            Cordialement,
                    </div>"""
        values = {
            'subject': f"{self.affaire_id.full_name} - BE N°{order}",
            'email_from': EMAIL_FROM,
            'email_to': emails,
            'body_html': body,
            'model': 'production.bordereau',  # Modèle concerné
            'attachment_ids': [(6, 0, attachments)],
        }

        msg_id = mail_pool.create(values)
        # And then call send function of the mail.mail,
        if msg_id:
            mail_pool.send([msg_id])
        return self.write({'name': name, 'order': order, 'state': 'sent_client', 'date_client': datetime.today()})

    def get_return(self, fichier):
        url = LOCAL_REPORTS_DIRECTORY + fichier
        if url:
            return {
                "type": "ir.actions.act_url",
                "target": "new",
                "url": url,
                "nodestroy": True,
            }
        else:
            return True

    def action_print(self):
        filename = self.generate_bordereau()
        return self.get_return(filename)

    def generate_bordereau(self, numero=None, send_client=False):
        filename = 'bordereau.xlsx'

        path_file = os.path.join(LOCAL_DIRECTORY, filename)
        workbook = openpyxl.load_workbook(path_file)
        worksheet = workbook['Modèle BE']
        if numero:
            order = numero
        elif self.order:
            order = self.order
        else:
            order = "*"
        worksheet['T2'] = order
        worksheet['P9'] = self.affaire_id.partner_id.name
        worksheet['A10'] = 'N° Affaire : {}'.format(self.affaire_id.number)
        worksheet['A11'] = 'Objet : {}'.format(self.affaire_id.name)
        worksheet['P11'] = self.affaire_id.directeur_travaux if self.affaire_id.directeur_travaux else ''
        worksheet['P13'] = datetime.now().strftime('%d/%m/%Y')
        x = 19
        for record in self.line_ids:
            if send_client:
                if record.state in ['validate']:
                    worksheet['A' + str(x)] = record.document_id.emetteur_id.name
                    worksheet['B' + str(x)] = record.document_id.zone_id.name if record.document_id.zone_id.name else ''
                    worksheet['C' + str(x)] = record.document_id.phase_id.name if record.document_id.phase_id.name else ''
                    worksheet['D' + str(x)] = record.document_id.ouvrage_id.name if record.document_id.ouvrage_id.name else ''
                    worksheet['E' + str(x)] = record.document_id.type_id.name if record.document_id.type_id.name else ''
                    worksheet['F' + str(x)] = record.document_id.numero
                    worksheet['G' + str(x)] = record.document_id.indice
                    worksheet['H' + str(x)] = record.document_id.name if record.document_id.name else ''
                    x = x + 1
            else:
                worksheet['A' + str(x)] = record.document_id.emetteur_id.name
                worksheet['B' + str(x)] = record.document_id.zone_id.name if record.document_id.zone_id.name else ''
                worksheet['C' + str(x)] = record.document_id.phase_id.name if record.document_id.phase_id.name else ''
                worksheet['D' + str(x)] = record.document_id.ouvrage_id.name if record.document_id.ouvrage_id.name else ''
                worksheet['E' + str(x)] = record.document_id.type_id.name if record.document_id.type_id.name else ''
                worksheet['F' + str(x)] = record.document_id.numero
                worksheet['G' + str(x)] = record.document_id.indice
                worksheet['H' + str(x)] = record.document_id.name if record.document_id.name else ''
                x = x + 1

        filename = "Bordereau_" + time.strftime("%H%M%S") + ".xlsx"
        path_file = os.path.join(LOCAL_DIRECTORY, filename)
        # Save the changes
        workbook.save(path_file)
        return filename

    def generate_bordereau_attachement(self, order=None, send_crt=False):
        # generate bordereau
        filename = self.generate_bordereau(order, send_crt)
        file_path = os.path.join(LOCAL_DIRECTORY, filename)
        # Lire le fichier depuis le répertoire
        try:
            with open(file_path, 'rb') as file:
                file_data = file.read()
            encoded_file = base64.b64encode(file_data)
        except FileNotFoundError:
            raise ValueError("Le fichier spécifié est introuvable.")

        # Créer une pièce jointe
        attachment = self.env['ir.attachment'].create({
            'name': filename,  # Nom du fichier
            'datas': encoded_file,  # Données encodées en base64
            'type': 'binary',
            'res_model': 'production.bordereau',  # Associez au modèle si nécessaire
        })
        return  attachment.id

class production_bordereau_line(models.Model):
    _name = 'production.bordereau.line'

    bordereau_id = fields.Many2one('production.bordereau', 'Bordereau', required=True)
    document_id = fields.Many2one('production.document', 'Document', required=True)
    note_ing = fields.Text('Note Ingénieur')
    note_crt = fields.Text('Note CRT')
    validate_ing = fields.Boolean("Validé par l'ingénieur?", default=False)
    validate_crt = fields.Boolean("Validé par la CRT?", default=False)
    state = fields.Selection(
        [('draft', 'Draft'), ('sent_crt', 'Envoyé CRT'), ('validate', 'Validé'), ('return', 'Retour Prod'),
         ('wait', 'En attente'), ('sent_client', 'Envoyé Client')], readonly=True, default='draft', copy=False,
        string="Etat")

    def action_cancel_ing(self):
        document_id = self.env['production.document'].search([('id', '=', self.document_id.id)])
        if document_id:
            note_ing = self.note_ing if self.note_ing else ''
            self._cr.execute('''Insert into production_document_note(document_id,user_id,date,note) 
                                   values({}, {}, '{}', '{}')'''.format(self.document_id.id, self.env.user.id,
                                                                        datetime.today(), note_ing))
            self._cr.commit()
            document_id.write({'state': 'return'})
        self.send_email_validation('Refus Ingénieur', 'refusé')
        return self.write({'state': 'return'})

    def action_cancel_crt(self):
        document_id = self.env['production.document'].search([('id', '=', self.document_id.id)])
        if document_id:
            note_crt = self.note_crt if self.note_crt else ''
            self._cr.execute('''Insert into production_document_note(document_id,user_id,date,note) 
                                   values({}, {}, '{}', '{}')'''.format(self.document_id.id, self.env.user.id,
                                                                        datetime.today(), note_crt))
            self._cr.commit()
            document_id.write({'state': 'wait'})
        self.send_email_validation('Refus CRT', 'refusé')
        return self.write({'state': 'wait'})

    def action_validate_ing(self):
        if self.validate_crt:
            self.write({'state': 'validate', 'validate_ing': True})
        else:
            self.write({'validate_ing': True})
        self.send_email_validation('Validation Ingénieur', 'validé')
        return True

    def action_validate_crt(self):
        if self.validate_ing:
            self.write({'state': 'validate', 'validate_crt': True})
        else:
            self.write({'validate_crt': True})
        self.send_email_validation('Validation CRT', 'validé')
        return True

    def get_emails(self):
        emails = []
        self._cr.execute("""select email,job.name from production_employee emp
                            inner join production_job job on job.id=emp.job_id
                            where job.name like 'CRT'""")
        for res in self._cr.fetchall():
            emails.append(res[0])
        self._cr.execute("""select email from production_employee where id=""" + str(self.bordereau_id.employee_id.id))
        for res in self._cr.fetchall():
            emails.append(res[0])
        self._cr.execute("""select email from production_employee where id=""" + str(self.bordereau_id.manager_id.id))
        for res in self._cr.fetchall():
            emails.append(res[0])
        emails = list(set(emails))
        emails = ','.join(emails)
        return  emails

    def send_email_validation(self, subject, status):
        """
        Envoie un e-mail de validation avec le statut du document.
        """
        if not self.document_id:
            raise UserError(_("Aucun document n'est associé pour l'envoi de l'e-mail."))

        # Préparer les données pour l'attachement
        attachment_ids = []
        if self.document_id:
            attach_data = {
                'name': self.document_id.filename,
                'datas': self.document_id.file,
                'res_model': 'production.document',
                'res_id': self.document_id.id,
                "type": "binary",
            }
            attachment = self.env['ir.attachment'].create(attach_data)
            attachment_ids.append(attachment.id)

        # Récupérer les e-mails des destinataires
        emails = self.get_emails()
        if not emails:
            raise UserError(_("Aucun e-mail n'a été trouvé pour les destinataires."))

        # Construire le corps de l'e-mail
        body_html = f"""
            <div style="margin: 0px; padding: 0px; font-size: 13px;">
                Bonjour,<br /><br />
                Le document <strong>{self.document_id.full_name}</strong> a été 
                <strong>{status}</strong> par l'utilisateur <strong>{self.env.user.name}</strong>.
                <br /><br />
                Cordialement,
            </div>
        """

        # Préparer les valeurs de l'e-mail
        email_values = {
            'subject': f"{self.document_id.full_name} - {subject}",
            'email_from': EMAIL_FROM,  # Fallback si l'utilisateur n'a pas d'e-mail
            'email_to': emails,
            'body_html': body_html,
            'model': 'production.document',
            'attachment_ids': [(6, 0, attachment_ids)] if attachment_ids else [],
        }

        # Créer et envoyer l'e-mail
        mail = self.env['mail.mail'].create(email_values)
        if mail:
            mail.send()

        return True

    def action_draft(self):
        document_obj = self.env['production.document'].search([('id', '=', self.document_id.id)])
        if document_obj:
            document_obj.write({'state': 'draft', 'bordereau_id': None})
            self.unlink()
        return True

    def action_open(self):
        return {
            "type": "ir.actions.act_window",
            "res_model": "production.document",
            "view_mode": "form",
            "view_type": "form",
            "res_id": self.id,
            "views": [
                (
                    self.env.ref("tectone.production_document_form_view").id,
                    "form",
                )
            ],
            "flags": {"form": {"action_buttons": True}},
        }

    def action_ing(self):
        return {
            "type": "ir.actions.act_window",
            "res_model": "production.bordereau.line",
            "view_mode": "form",
            "view_type": "form",
            "res_id": self.id,
            "views": [
                (
                    self.env.ref("tectone.production_bordereau_line_ing_form_view").id,
                    "form",
                )
            ],
            "target": "new",
            "flags": {"form": {"action_buttons": True}},
        }

    def action_crt(self):
        return {
            "type": "ir.actions.act_window",
            "res_model": "production.bordereau.line",
            "view_mode": "form",
            "view_type": "form",
            "res_id": self.id,
            "views": [
                (
                    self.env.ref("tectone.production_bordereau_line_crt_form_view").id,
                    "form",
                )
            ],
            "target": "new",
            "flags": {"form": {"action_buttons": True}},
        }

class production_pointage(models.Model):
    _name = 'production.pointage'
    _order = 'date desc'

    def _default_employee(self):
        employee_obj = self.env['production.employee'].search([('user_id', '=', self.env.user.id)])
        if employee_obj:
            return employee_obj.id
        return False

    name = fields.Char(string="N°", default="*", readonly=True, help="Pointage")
    date = fields.Date('Date', required=True, default=datetime.today(), readonly=True,
                       states={'draft': [('readonly', False)]})
    employee_id = fields.Many2one('production.employee', 'Nom et Prénom', default=_default_employee, required=True,
                                  readonly=True)
    line_ids = fields.One2many('production.pointage.line', 'pointage_id', 'Pointages', readonly=True,
                               states={'draft': [('readonly', False)]})
    nb_hour = fields.Float(compute='_compute_nb_hour', string="Nombre d'heures")
    state = fields.Selection(
        [('draft', 'Draft'), ('sent', 'Sent')], readonly=True, default='draft', copy=False, string="Etat")
    _sql_constraints = [('uniq_pointage', 'unique(date, employee_id)', "Le pointage quotidien est unique par employé!"),]

    @api.model
    def create(self, values):
        values['name'] = self.env['ir.sequence'].get('production.pointage') or ' '
        res = super(production_pointage, self).create(values)
        return res

    def _compute_nb_hour(self):
        for record in self:
            nb_hour = 0
            for line in record.line_ids:
                nb_hour += line.hour
            record.nb_hour = nb_hour

    def action_draft(self):
        return self.write({'state': 'draft'})

    def action_sent(self):
        if len(self.line_ids) == 0:
            raise ValidationError(_("Cette action exige d'avoir saisir au moins une ligne de pointage"))
        return self.write({'state': 'sent'})

    def unlink(self):
        for record in self:
            if record.state not in ('draft'):
                raise UserError("Vous ne pouvez pas supprimer un document qui n'est pas à l'état de brouillon!")
        return super(production_document, self).unlink()

class production_pointage_line(models.Model):
    _name = 'production.pointage.line'

    pointage_id = fields.Many2one('production.pointage', 'Pointage')
    affaire_id = fields.Many2one('production.affaire', 'Affaire', required=True)
    type = fields.Selection([('meeting', 'Réunion'), ('document', 'Document'), ('research', 'Recherche'), ('modelisation_cao', 'Modélisation CAO'), ('modelisation_calcul', 'Modélisation Calcul'), ('stand', 'Stand-By'), ('other', 'Autre')], 'Type',
                            required=True)
    reunion_id = fields.Many2one('production.reunion', 'Réunion')
    document_id = fields.Many2one('production.document', 'Document')
    task = fields.Char('Tâche')
    nb_hour = fields.Selection([('0.5', '1/2h'),
                                ('1', '1h'), ('1.5', '1.5h'),
                                ('2', '2h'), ('2.5', '2.5h'),
                                ('3', '3h'), ('3.5', '3.5h'),
                                ('4', '4h'), ('4.5', '4.5h'),
                                ('5', '5h'), ('5.5', '5.5h'),
                                ('6', '6h'), ('6.5', '6.5h'),
                                ('7', '7h'), ('7.5', '7.5h'),
                                ('8', '8h'), ('8.5', '8.5h')], "Nb d'heure", required=True)
    hour = fields.Float("Nb d'heure")

    @api.model
    def create(self, values):
        hour = float(values.get('hour', 0))
        pointage_id = values.get('pointage_id')

        if not pointage_id:
            raise ValidationError(_("Pointage ID non spécifié."))

        # Récupérer l'objet pointage associé
        pointage_obj = self.env['production.pointage'].browse(pointage_id)
        if not pointage_obj.exists():
            raise ValidationError(_("Pointage non trouvé pour l'ID spécifié."))

        # Calculer le total des heures déjà enregistrées pour ce pointage
        existing_hours = sum(float(line.hour) for line in pointage_obj.line_ids)

        # Ajouter les heures en cours de saisie
        total_hours = existing_hours + hour

        # Vérification de la limite des heures
        if total_hours > 12:
            raise ValidationError(
                _(f'Le nombre total d\'heures pointées pour une journée ne doit pas dépasser 12 heures maximum. '
                  f'Actuellement : {total_hours} heures.')
            )

        res = super(production_pointage_line, self).create(values)
        return res

    def write(self, values):
        for record in self:
            # Récupération de l'heure mise à jour ou l'heure actuelle
            new_hour = float(values.get('hour', record.hour))

            # Récupération du pointage lié
            pointage_id = values.get('pointage_id', record.pointage_id.id)
            pointage_obj = self.env['production.pointage'].browse(pointage_id)

            if not pointage_obj.exists():
                raise ValidationError(_("Pointage non trouvé pour l'ID spécifié."))

            # Calcul des heures totales en excluant l'enregistrement actuel
            existing_hours = sum(float(line.hour) for line in pointage_obj.line_ids if line.id != record.id)

            # Ajouter les nouvelles heures en cours de modification
            total_hours = existing_hours + new_hour

            # Vérification de la limite des heures
            if total_hours > 12:
                raise ValidationError(
                    _(f'Le nombre total d\'heures pointées pour une journée ne doit pas dépasser 12 heures maximum. '
                      f'Actuellement : {total_hours} heures.')
                )

        # Appel de la méthode write originale
        res = super(production_pointage_line, self).write(values)
        return res

    @api.onchange('nb_hour')
    def _onchange_nb_hour(self):
        self.hour = float(self.nb_hour)

class production_tbd(models.Model):
    _name = 'production.tbd'
    _rec_name = 'affaire_id'

    name = fields.Char('TBD')
    affaire_id = fields.Many2one('production.affaire', 'Affaire')
    amount_contract = fields.Float('Montant Affaire', currency_field='currency_id', readonly=False)
    amount_avenant = fields.Float('Montant Avenant', currency_field='currency_id', readonly=False)
    amount_billed = fields.Float('Montant Facturé', currency_field='currency_id', readonly=False)
    amount_payed = fields.Float('Montant Payé', currency_field='currency_id', readonly=False)
    percentage_billed = fields.Float('% Facturé', readonly=False)
    percentage_payed = fields.Float('% Payé', readonly=False)
    currency_id = fields.Many2one('res.currency', readonly=False, string='Devise')
    livrable_ids = fields.One2many('production.tbd.livrable', 'tbd_id', 'Livrables', readonly=True)
    livrable_time_ids = fields.One2many('production.tbd.livrable.time', 'tbd_id', 'Livrables', readonly=True)
    other_ids = fields.One2many('production.tbd.other', 'tbd_id', 'Autres', readonly=True)
    other_time_ids = fields.One2many('production.tbd.other.time', 'tbd_id', 'Autres', readonly=True)
    ratio_ids = fields.One2many('production.tbd.ratio', 'tbd_id', 'ratios', readonly=True)
    document_ids = fields.One2many('production.tbd.document', 'tbd_id', 'Documents', readonly=True)

    # -------------------------------------------------------------------------
    # ONCHANGE METHODS
    # -------------------------------------------------------------------------
    @api.onchange('affaire_id')
    def onchange_affaire_id(self):
        if self.affaire_id:
            affaire_id = self.affaire_id.id
            self._cr.execute('''delete from production_tbd_livrable''')
            self._cr.commit()
            self._cr.execute('''delete from production_tbd_livrable_time''')
            self._cr.commit()
            self._cr.execute('''delete from production_tbd_other''')
            self._cr.commit()
            self._cr.execute('''delete from production_tbd_other_time''')
            self._cr.commit()
            self._cr.execute('''delete from production_tbd_ratio''')
            self._cr.commit()
            self._cr.execute('''delete from production_tbd_document''')
            self._cr.commit()
            affaire_obj = self.env['production.affaire'].search([('id', '=', affaire_id)], limit=1)
            self.affaire_id = affaire_obj.id
            self.amount_contract = affaire_obj.amount_contract
            self.amount_avenant = affaire_obj.amount_avenant
            self.amount_billed = affaire_obj.amount_billed
            self.amount_payed = affaire_obj.amount_payed
            self.currency_id = affaire_obj.currency_id
            if self.amount_contract + self.amount_avenant == 0:
                self.percentage_billed = 0
            else:
                self.percentage_billed = round(self.amount_billed / (self.amount_contract + self.amount_avenant), 2)
            if self.amount_billed == 0:
                self.percentage_payed = 0
            else:
                self.percentage_payed = round(self.amount_payed / self.amount_billed, 2)

            livrable_ids = []
            other_ids = []
            self._cr.execute("""select pdt.name,
                                case when t3.prev is null then 0 else t3.prev end as prev,
                                case when t3.exe is null then 0 else t3.exe end as exe,
                                case when t3.indice is null then 0 else t3.indice end as indice,
                                case when t3.exe is null or t3.prev=0 or t3.exe=0 then 0 else round(100.00 * t3.exe/t3.prev) end
                                from production_document_type pdt left join(
                                    select case when t1.type_id is not null then t1.type_id else t2.type_id end,prev,exe,indice from(
                                    select affaire_id,type_id,prev from production_affaire_document_type
                                    where affaire_id = {}) as t1
                                    full outer join(
                                    select affaire_id,type_id,count(distinct pd.id) as exe,count(distinct pdi.id) as indice from production_document pd
                                    inner join production_document_indice pdi on pd.id=pdi.document_id
                                    where affaire_id = {}
                                    group by affaire_id,type_id) as t2 on t1.type_id=t2.type_id
								) as t3 on t3.type_id=pdt.id
                                order by pdt.sequence""".format(affaire_id, affaire_id))
            for row in self._cr.fetchall():
                livrable_ids.append((0, 0, {'modele': row[0],
                                            'prev': row[1],
                                            'exe': row[2],
                                            'indice': row[3],
                                            'percentage': row[4]}))
            self._cr.execute("""select name,0,0,0 from production_reunion order by sequence""".format(affaire_id, affaire_id))
            for row in self._cr.fetchall():
                other_ids.append((0, 0, {'modele': row[0],
                                            'prev': row[1],
                                            'exe': row[2],
                                            'percentage': row[3]}))
            for pointage_name in ['Modélisation CAO', 'Modélisation Calcul', 'Recherche', 'Stand by', 'Autre']:
                other_ids.append((0, 0, {'modele': pointage_name, 'prev': 0, 'exe': 0, 'percentage': 0}))
            livrable_time_ids = []
            other_time_ids = []
            self._cr.execute("""select pdt.name,case when t2.nb_hour_ing is null then 0 else t2.nb_hour_ing end,
                                case when t2.nb_hour_proj is null then 0 else t2.nb_hour_proj end
                                from production_document_type pdt
                                left join(
                                select pd.type_id,t1.affaire_id,t1.document_id,t1.nb_hour_ing,nb_hour_proj from production_document pd
                                inner join(
                                select b.affaire_id,b.document_id,a.employee_id,
                                    sum(case when job.name like 'Ing%' then b.hour else 0 end) as nb_hour_ing,
                                    sum(case when job.name like 'Proj%' then b.hour else 0 end) as nb_hour_proj 
                                from production_pointage a
                                inner join production_pointage_line b on a.id=b.pointage_id
                                inner join production_employee emp on emp.id=a.employee_id
                                inner join production_job job on job.id=emp.job_id
                                where b.type like 'document'
                                and a.state = 'sent'
                                and b.affaire_id={}
                                group by b.affaire_id,b.document_id,a.employee_id
                                ) as t1 on t1.document_id=pd.id) as t2
                                on t2.type_id = pdt.id
                                order by pdt.sequence""".format(affaire_id))
            for row in self._cr.fetchall():
                livrable_time_ids.append((0, 0, {'h_ing': row[1], 'h_proj': row[2], }))
            self._cr.execute("""select r.name,case when t2.nb_hour_ing is null then 0 else t2.nb_hour_ing end,
                                case when t2.nb_hour_proj is null then 0 else t2.nb_hour_proj end
                                from production_reunion r
                                left join(
                                select b.affaire_id,b.reunion_id,a.employee_id,
                                    sum(case when job.name like 'Ing%' then b.hour else 0 end) as nb_hour_ing,
                                    sum(case when job.name like 'Proj%' then b.hour else 0 end) as nb_hour_proj from production_pointage a
                                inner join production_pointage_line b on a.id=b.pointage_id
                                inner join production_employee emp on emp.id=a.employee_id
                                inner join production_job job on job.id=emp.job_id
                                where b.type like 'meeting'
                                and a.state = 'sent'
                                and b.affaire_id={}
                                group by b.affaire_id,b.reunion_id,a.employee_id) as t2
                                on t2.reunion_id = r.id
								order by r.sequence""".format(affaire_id))
            for row in self._cr.fetchall():
                other_time_ids.append((0, 0, {'h_ing': row[1], 'h_proj': row[2], }))
            for (pointage_name, pointage_type) in [('modelisation_cao', 'Modélisation CAO'), ('modelisation_calcul', 'Modélisation Calcul'),
                                                   ('Recherche', 'research'), ('Stand by', 'stand'), ('Autre', 'other')]:
                self._cr.execute(f""" select '{pointage_type}',
                                                    sum(case when job.name like 'Ing%' then b.hour else 0 end) as nb_hour_ing,
                                                    sum(case when job.name like 'Proj%' then b.hour else 0 end) as nb_hour_proj 
                                                from production_pointage a
                                                inner join production_pointage_line b on a.id=b.pointage_id
                                                inner join production_employee emp on emp.id=a.employee_id
                                                inner join production_job job on job.id=emp.job_id
                                                where b.type like '{pointage_name}'
                                                and a.state = 'sent'
                                                and b.affaire_id={affaire_id}
                                                group by b.affaire_id,b.document_id,a.employee_id""")
                row = self._cr.fetchone()
                if row:
                    other_time_ids.append((0, 0, {'h_ing': row[1], 'h_proj': row[2], }))
                else:
                    other_time_ids.append((0, 0, {'h_ing': 0, 'h_proj': 0, }))
            ratio_ids = []
            self._cr.execute(
                """select employee_id,sum(ppl.hour) as hour from production_pointage pp
                    inner join production_pointage_line ppl on pp.id=ppl.pointage_id
                    where ppl.affaire_id = {}
                    and pp.state = 'sent'
                    group by employee_id""".format(affaire_id))
            for row in self._cr.fetchall():
                ratio_ids.append((0, 0, {'employee_id': row[0], 'h_prod': row[1], }))
            document_ids = []
            records = self.env['production.affaire.document'].search([('affaire_id', '=', affaire_obj.id)])
            for record in records:
                document_ids.append((0, 0, {'filename': record.filename, 'file': record.file, }))

            self.livrable_ids = livrable_ids
            self.livrable_time_ids = livrable_time_ids
            self.other_ids = other_ids
            self.other_time_ids = other_time_ids
            self.ratio_ids = ratio_ids
            self.document_ids = document_ids

class production_tbd_livrable(models.Model):
    _name = 'production.tbd.livrable'

    tbd_id = fields.Many2one('production.tbd', 'TBD')
    modele = fields.Char('Modèle')
    prev = fields.Integer('PREV')
    exe = fields.Integer('EXE')
    indice = fields.Integer('IND')
    percentage = fields.Float('%')

class production_tbd_other(models.Model):
    _name = 'production.tbd.other'

    tbd_id = fields.Many2one('production.tbd', 'TBD')
    modele = fields.Char('Modèle')
    prev = fields.Integer('PREV')
    exe = fields.Integer('EXE')
    indice = fields.Integer('IND')
    percentage = fields.Float('%')

class production_tbd_livrable_time(models.Model):
    _name = 'production.tbd.livrable.time'

    tbd_id = fields.Many2one('production.tbd', 'TBD')
    h_ing = fields.Float('INGENIEURS')
    h_proj = fields.Float('PROJETEURS')

class production_tbd_other_time(models.Model):
    _name = 'production.tbd.other.time'

    tbd_id = fields.Many2one('production.tbd', 'TBD')
    h_ing = fields.Float('INGENIEURS')
    h_proj = fields.Float('PROJETEURS')

class production_tbd_ratio(models.Model):
    _name = 'production.tbd.ratio'

    tbd_id = fields.Many2one('production.tbd', 'TBD')
    employee_id = fields.Many2one('production.employee', 'Nom et Prénom')
    h_prod = fields.Float('H.Prod')

class production_tbd_document(models.Model):
    _name = 'production.tbd.document'

    tbd_id = fields.Many2one('production.tbd', 'TBD')
    filename = fields.Char("Nom du fichier", size=256)
    file = fields.Binary("Fichier")

class production_bordereau_crt(models.Model):
    _name = 'production.bordereau.crt'

    affaire_id = fields.Many2one('production.affaire', 'Affaire', required=True, readonly=True)
    emetteur_id = fields.Many2one('production.emetteur', 'Emetteur', required=True, readonly=True)
    type_id = fields.Many2one('production.document.type', 'Type Document', required=True, readonly=True)
    indice = fields.Char('Indice', required=True, readonly=True)
    document_id = fields.Many2one('production.document', 'Document', required=True, readonly=True)
    document_identifiant = fields.Char('Identifiant Document', required=True, readonly=True)

    state = fields.Selection(
        [('draft', 'Draft'), ('cancel1', 'Cancel1'), ('validate1', 'Validate1'), ('cancel2', 'Cancel2'),
         ('sent', 'Sent')], readonly=True, default='draft', copy=False, string="Etat")
