# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
import re
from odoo import api, models, fields, _, SUPERUSER_ID
from odoo.exceptions import AccessError, UserError
from datetime import datetime


class production_affaire(models.Model):
    _name = 'production.affaire'
    _description = 'Affaires'
    _rec_name = 'full_name'
    _order = 'number desc'

    def _default_number(self):
        number = 1
        affaire_id = self.env['production.affaire'].search([], order='number desc', limit=1)
        if affaire_id:
            number = affaire_id.number + 1
        return number

    full_name = fields.Char(string='Affaire', readonly=True, compute='_compute_full_name', store=True)
    no_affaire = fields.Char('N° Affaire')
    name = fields.Char('Désignation')
    number = fields.Integer("N° Affaire", default=_default_number)
    year = fields.Char('Année', size=4, default=datetime.today().year, required=True)
    directeur_travaux = fields.Char('Référent client')
    type = fields.Selection([('contract', 'Contrat'),('marche', 'Marché'), ('bc', 'Bon de commande')], 'Type')
    partner_id = fields.Many2one('res.partner', 'Client', domain=[('is_company','=', True)])
    no_contract = fields.Char('N° Contrat')
    amount_contract = fields.Float('Montant Affaire', currency_field='currency_id')
    amount_avenant = fields.Float('Montant Avenant', currency_field='currency_id')
    amount_billed = fields.Float(string='Montant Facturé', readonly=True, compute='_compute_total', currency_field='currency_id')
    amount_payed = fields.Float(string='Montant Payé', readonly=True, compute='_compute_total', currency_field='currency_id')
    percentage_billed = fields.Float(string='% Facturé', readonly=True, compute='_compute_percentage')
    percentage_payed = fields.Float(string='% Payé', readonly=True, compute='_compute_percentage')
    document_ids = fields.One2many("production.affaire.document", "affaire_id", string="Documents", copy=False)
    invoice_ids = fields.One2many("production.affaire.invoice", "affaire_id", string="Factures", copy=False)
    payment_ids = fields.One2many("production.affaire.payment", "affaire_id", string="Paiements", copy=False)
    email_ids = fields.One2many("production.affaire.email", "affaire_id", string="Emails", copy=False)
    email_cc_ids = fields.One2many("production.affaire.email.cc", "affaire_id", string="Emails", copy=False)
    plan_ids = fields.One2many("production.document", "affaire_id", string="Documents", copy=False)
    zone_ids = fields.One2many("production.zone", "affaire_id", string="Zones", copy=False)
    document_type_ids = fields.One2many("production.affaire.document.type", "affaire_id", string="Types Documents", copy=True)
    production_document_ids = fields.One2many("production.document", "affaire_id", string="Documents")
    currency_id = fields.Many2one('res.currency', string='Devise', required=True)
    phase_id = fields.Many2one('production.phase', 'Type de marché')
    phase_ids = fields.Many2many('production.phase', 'rel_affaire_phase', 'phase_id', 'affaire_id', 'Phases')
    zone_id_required = fields.Boolean('Zone required', default=True)
    zone_id_visible = fields.Boolean('Zone Visible', default=True)
    phase_id_visible = fields.Boolean('Phase Visible', default=True)
    scope_id_required = fields.Boolean('Scope required', default=True)
    scope_id_visible = fields.Boolean('Scope Visible', default=True)
    type_id_required = fields.Boolean('Type required', default=True)
    type_id_visible = fields.Boolean('Type Visible', default=True)
    ouvrage_id_required = fields.Boolean('Ouvrage required', default=True)
    ouvrage_id_visible = fields.Boolean('Ouvrage Visible', default=True)

    @api.model
    def create(self, values):
        affaire = super(production_affaire, self).create(values)
        # create zone
        self.env['production.zone'].create({'affaire_id': affaire.id,
                                           'name': 'TZO',
                                           'from_indice': 1,
                                           'to_indice': 1})

        for record in self.env['production.document.type'].search([]):
            self.env['production.affaire.document.type'].create({'affaire_id': affaire.id,
                                                'type_id': record.id,
                                                'prev': 0 })

        return affaire

    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=100):
        args = args or []
        recs = self.browse()

        # Si aucune correspondance n'est trouvée dans les affaires
        if not recs:
            # Recherche directe dans le modèle des affaires
            recs = self.search([
                                   '|', '|', '|',
                                   ('full_name', operator, name),  # Recherche dans le champ "name"
                                   ('name', operator, name),  # Recherche dans le champ "name"
                                   ('number', operator, name),  # Recherche dans le champ "number"
                                   ('year', operator, name)  # Recherche dans le champ "year"
                               ] + args, limit=limit)

            # Recherche via les phases Many2many
            if not recs and name:
                phase_model = self.env['production.phase']  # Modèle des phases
                # Recherche des phases correspondant au terme
                phase_recs = phase_model.search([('name', operator, name)], limit=limit)
                if phase_recs:
                    # Récupérer les affaires liées aux phases trouvées
                    affaire_ids = self.search([('phase_ids', 'in', phase_recs.ids)] + args, limit=limit)
                    recs |= affaire_ids  # Ajouter les affaires trouvées via les phases

            # Recherche via le partenaire (Many2one)
            if not recs and name:
                partner_model = self.env['res.partner']  # Modèle des partenaires
                # Recherche des partenaires correspondant au terme
                partner_recs = partner_model.search([('name', operator, name)], limit=limit)
                if partner_recs:
                    # Récupérer les affaires liées aux partenaires trouvés
                    affaire_ids = self.search([('partner_id', 'in', partner_recs.ids)] + args, limit=limit)
                    recs |= affaire_ids  # Ajouter les affaires trouvées via les partenaires

        return recs.name_get()
    # -------------------------------------------------------------------------
    # COMPUTE METHODS
    # -------------------------------------------------------------------------

    @api.depends('year', 'number', 'partner_id', 'phase_ids', 'name')
    def _compute_full_name(self):
        for record in self:
            full_name = ''
            if record.year and len(record.year)==4:
                full_name = record.year[2:]
            if record.number:
                full_name += f'-{record.number}'
            if record.partner_id.ref:
                full_name += f'-{record.partner_id.ref}'
            else:
                full_name += f'-{record.partner_id.name}'
            if record.phase_ids:
                for phase in record.phase_ids:
                    full_name += f'-{phase.name}'
            full_name += f'-{record.name}'
            record.full_name = full_name

    @api.depends('invoice_ids', 'payment_ids', 'amount_contract')
    def _compute_percentage(self):
        for record in self:
            amount_billed = 0.0
            amount_payed = 0.0
            percentage_billed = 0.0
            percentage_payed = 0.0
            for rec in record.invoice_ids:
                amount_billed += rec.amount
            for rec in record.payment_ids:
                amount_payed += rec.amount
            if record.amount_contract and record.amount_contract > 0:
                percentage_billed = round((amount_billed * 1.00) / record.amount_contract, 2)
            if record.amount_contract and record.amount_contract > 0:
                percentage_payed = round((amount_payed * 1.00) / record.amount_contract, 2)
            record.percentage_billed = percentage_billed
            record.percentage_payed = percentage_payed

    @api.depends('invoice_ids', 'payment_ids')
    def _compute_total(self):
        for record in self:
            amount_billed = 0.0
            amount_payed = 0.0
            for rec in record.invoice_ids:
                amount_billed += rec.amount
            for rec in record.payment_ids:
                amount_payed += rec.amount
            record.amount_billed = amount_billed
            record.amount_payed = amount_payed

    _sql_constraints = [
        ('name_uniq', 'UNIQUE (number)', "Le numéro de l'affaire est unique!"),
    ]

class production_affaire_document(models.Model):
    _name = "production.affaire.document"
    _description = "Documents des affaires"

    affaire_id = fields.Many2one("production.affaire", "Affaire")
    filename = fields.Char("Nom du fichier", size=256)
    file = fields.Binary("Fichier")

class production_affaire_invoice(models.Model):
    _name = "production.affaire.invoice"
    _description = "Factures des affaires"

    affaire_id = fields.Many2one("production.affaire", "Affaire")
    name = fields.Char('N° facture')
    date = fields.Date('Date facture')
    amount = fields.Float('Montant facturé', currency_field='currency_id')
    currency_id = fields.Many2one(related='affaire_id.currency_id', store=True, readonly=True)

class production_affaire_payment(models.Model):
    _name = "production.affaire.payment"
    _description = "Paiements des affaires"

    affaire_id = fields.Many2one("production.affaire", "Affaire")
    name = fields.Char('N° paiement')
    date = fields.Date('Date de paiement')
    amount = fields.Float('Montant payé', currency_field='currency_id')
    currency_id = fields.Many2one(related='affaire_id.currency_id', store=True, readonly=True)

class production_affaire_document_type(models.Model):
    _name = "production.affaire.document.type"
    _description = "Types Documents"

    affaire_id = fields.Many2one("production.affaire", "Affaire", required=True, readonly=True)
    type_id = fields.Many2one("production.document.type", "Identifiant Document", required=True, readonly=True)
    prev = fields.Integer('Prévus')

    _sql_constraints = [
        ('name_uniq', 'UNIQUE (affaire_id,type_id)', 'Le couple [affaire,Identifiant de document] est unique!'),
    ]

class production_affaire_email(models.Model):
    _name = "production.affaire.email"
    _description = "Emails"

    affaire_id = fields.Many2one("production.affaire", "Affaire")
    name = fields.Char("Email", required=True)

    _sql_constraints = [
        ('name_uniq', 'UNIQUE (affaire_id,name)', 'Le couple [affaire,email] est unique!'),
    ]

    def is_valid_email(self, email):
        # Définition de l'expression régulière pour une adresse e-mail
        email_regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(email_regex, email) is not None

    @api.model
    def create(self, values):
        email = values.get('name', None)
        if email and not self.is_valid_email(email):
            raise UserError(_(f"La valeur saisie <{email}> ne correspond pas à une adresse email valide."))
        record = super(production_affaire_email, self).create(values)
        return record

    def write(self, values):
        email = values.get('name', None)
        if email and not self.is_valid_email(email):
            raise UserError(_(f"La valeur saisie <{email}> ne correspond pas à une adresse email valide."))
        res = super(production_affaire_email, self).write(values)
        return res


class production_affaire_email_cc(models.Model):
    _name = "production.affaire.email.cc"
    _description = "Emails"

    affaire_id = fields.Many2one("production.affaire", "Affaire")
    name = fields.Char("Email", required=True)

    _sql_constraints = [
        ('name_uniq', 'UNIQUE (affaire_id,name)', 'Le couple [affaire,email] est unique!'),
    ]

    def is_valid_email(self, email):
        # Définition de l'expression régulière pour une adresse e-mail
        email_regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(email_regex, email) is not None

    @api.model
    def create(self, values):
        email = values.get('name', None)
        if email and not self.is_valid_email(email):
            raise UserError(_(f"La valeur saisie <{email}> ne correspond pas à une adresse email valide."))
        record = super(production_affaire_email_cc, self).create(values)
        return record

    def write(self, values):
        email = values.get('name', None)
        if email and not self.is_valid_email(email):
            raise UserError(_(f"La valeur saisie <{email}> ne correspond pas à une adresse email valide."))
        res = super(production_affaire_email_cc, self).write(values)
        return res


class production_zone(models.Model):
    _name = "production.zone"
    _description = "Zones"
    _order = "from_indice"

    affaire_id = fields.Many2one("production.affaire", "Affaire")
    name = fields.Char("Zone", size=256, required=True)
    need_plage = fields.Boolean('Besoin de plage de numéros?')
    from_indice = fields.Integer('De', default = 1)
    to_indice = fields.Integer('A', default = 1)

    _sql_constraints = [
        ('name_uniq', 'UNIQUE (affaire_id, name)', "Le nom de la zone est unique par affaire!"),
        ('indice_check', "CHECK ((from_indice <= to_indice))", "L'indice 'Au' doit être supérieur à l'indice 'Du'."),
    ]

    @api.model
    def create(self, values):
        affaire_id = values.get('affaire_id')
        from_indice = values.get('from_indice')
        to_indice = values.get('to_indice')
        name = values.get('name')
        if from_indice > to_indice:
            raise UserError(_("L'indice 'A' doit être supérieur ou égal à l'indice 'B"))
        res = super(production_zone, self).create(values)
        return res

    def write(self, values):
        res = super(production_zone, self).write(values)
        return res

    def unlink(self):
        for record in self:
            if record.name == 'TZO':
                raise UserError("La zone <TZO> ne peut être supprimée")
        return super(production_zone, self).unlink()

    def action_delete(self):
        return self.unlink()



