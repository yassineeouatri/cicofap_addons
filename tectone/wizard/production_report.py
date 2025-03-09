import datetime
import os
import time
import copy
import xlsxwriter
from odoo import models, fields, api, _
from odoo.exceptions import UserError

PASSWORD = "cestsecret"
SERVER_ADRESS = 'http://192.168.0.35'
SERVER_ADRESS = 'http://localhost:8069'
SERVER_ADRESS = 'https://erp.tectone.ma'
EMAIL_FROM = 'tectonegroup@outlook.com'
LOCAL_DIRECTORY = "C://Program Files//Odoo15//server//odoo//addons//web//static//reports"
LOCAL_DIRECTORY = "C://Users//Yassine//PycharmProjects//cicofap//Scripts//odoo//addons//web//static//reporting//"
LOCAL_DIRECTORY = "/opt/odoo/odoo/addons/web/static/report/"
LOCAL_REPORTS_DIRECTORY = "/web/static/reports/"
LOCAL_REPORTS_DIRECTORY = "web/static/reporting/"
LOCAL_REPORTS_DIRECTORY = "web/static/report/"

class ProductionReportPrint(models.TransientModel):
    _name = "production.report.print"
    _description = "Generate production report"
    _rec_name = 'affaire_id'

    affaire_id = fields.Many2one('production.affaire', 'Affaire')

    def action_print_report_fin(self):
        if self.affaire_id:
            filename = "Rapport financier - " + str(self.affaire_id.number)+ " - "+ time.strftime("%H%M%S") + ".xlsx"
            search_ids = [('id', '=', self.affaire_id.id)]
        else:
            filename = "Rapport financier - " + time.strftime("%H%M%S") + ".xlsx"
            search_ids = []

        workbook = xlsxwriter.Workbook(LOCAL_DIRECTORY + filename)
        style_title = workbook.add_format(
            {
                "bg_color": "#003366",
                "color": "white",
                "text_wrap": True,
                "bold": 1,
                "align": "center",
                "valign": "vcenter",
                "top": 1,
                "bottom": 1,
            }
        )
        style = workbook.add_format(
            {
                "text_wrap": True,
                "bold": 1,
                "align": "center",
                "valign": "vcenter",
                "top": 1,
                "bottom": 1,
            }
        )
        style_number = workbook.add_format(
            {
                "num_format": "#,##0.00",
                "text_wrap": True,
                "align": "center",
                "valign": "vcenter",
                "top": 1,
                "bottom": 1,
            }
        )
        style_percentage = workbook.add_format(
            {
                "num_format": "#,##0.00%",
                "text_wrap": True,
                "align": "center",
                "valign": "vcenter",
                "top": 1,
                "bottom": 1,
            }
        )
        sheet = workbook.add_worksheet("Données financières")
        sheet.protect(password=PASSWORD)
        sheet.set_zoom(85)
        sheet.set_tab_color("yellow")
        sheet.set_column("A:F", 15)
        x = 1
        sheet.write("A" + str(x), "Montant contrat", style_title)
        sheet.write("B" + str(x), "Montant avenant", style_title)
        sheet.write("C" + str(x), "Montant facturé", style_title)
        sheet.write("D" + str(x), "Montant payé", style_title)
        sheet.write("E" + str(x), "% facturé", style_title)
        sheet.write("F" + str(x), "% payé", style_title)
        x = 2
        for affaire in self.env['production.affaire'].search(search_ids, order='name desc'):
            if affaire.amount_contract + affaire.amount_avenant == 0:
                percentage_billed = 0
            else:
                percentage_billed = round(affaire.amount_billed * 1.00 / (affaire.amount_contract + affaire.amount_avenant), 2)
            if affaire.amount_billed == 0:
                percentage_payed = 0
            else:
                percentage_payed = round(affaire.amount_payed * 1.00 / affaire.amount_billed, 2)
            sheet.merge_range("A" + str(x) + ':F'+str(x), affaire.full_name, style)
            x = x + 1
            sheet.write_number("A" + str(x), affaire.amount_contract, style_number)
            sheet.write_number("B" + str(x), affaire.amount_avenant, style_number)
            sheet.write_number("C" + str(x), affaire.amount_billed, style_number)
            sheet.write_number("D" + str(x), affaire.amount_payed, style_number)
            sheet.write("E" + str(x), affaire.percentage_billed, style_percentage)
            sheet.write("F" + str(x), affaire.percentage_payed, style_percentage)
            x = x + 1
        workbook.close()

        return self.get_return(filename)

    def action_print_report__prod(self):
        if self.affaire_id:
            filename = "Rapport production - " + str(self.affaire_id.number)+ " - "+ time.strftime("%H%M%S") + ".xlsx"
            search_ids = [('id', '=', self.affaire_id.id)]
        else:
            filename = "Rapport production - " + time.strftime("%H%M%S") + ".xlsx"
            search_ids = []

        workbook = xlsxwriter.Workbook(LOCAL_DIRECTORY + filename)
        format_standard = {
            "text_wrap": True,
            "align": "center",
            "valign": "vcenter",
            "top": 1,
            "bottom": 1,
        }

        # Crée des copies séparées pour chaque format
        format_title = copy.deepcopy(format_standard)
        format_title['bg_color'] = '#003366'
        format_title['color'] = 'white'
        format_text = copy.deepcopy(format_standard)
        format_text_green = copy.deepcopy(format_text)
        format_text_green['color'] = 'green'
        format_text_red = copy.deepcopy(format_text)
        format_text_red['color'] = 'red'
        format_text_orange = copy.deepcopy(format_text)
        format_text_orange['color'] = 'orange'

        format_number = copy.deepcopy(format_standard)
        format_number['num_format'] = "#,##0.00"
        format_number_green = copy.deepcopy(format_number)
        format_number_green['color'] = 'green'
        format_number_red = copy.deepcopy(format_number)
        format_number_red['color'] = 'red'
        format_number_orange = copy.deepcopy(format_number)
        format_number_orange['color'] = 'orange'

        format_percentage = copy.deepcopy(format_standard)
        format_percentage['num_format'] = "#,##0.00%"
        format_percentage_green = copy.deepcopy(format_percentage)
        format_percentage_green['color'] = 'green'
        format_percentage_red = copy.deepcopy(format_percentage)
        format_percentage_red['color'] = 'red'
        format_percentage_orange = copy.deepcopy(format_percentage)
        format_percentage_orange['color'] = 'orange'

        # Application des formats au style Excel
        style_title = workbook.add_format(format_title)
        style = workbook.add_format(format_text)
        style_green = workbook.add_format(format_text_green)
        style_red = workbook.add_format(format_text_red)
        style_orange = workbook.add_format(format_text_orange)
        style_number = workbook.add_format(format_number)
        style_number_green = workbook.add_format(format_number_green)
        style_number_red = workbook.add_format(format_number_red)
        style_number_orange = workbook.add_format(format_number_orange)
        style_percentage = workbook.add_format(format_percentage)
        style_percentage_green = workbook.add_format(format_percentage_green)
        style_percentage_red = workbook.add_format(format_percentage_red)
        style_percentage_orange = workbook.add_format(format_percentage_orange)
        sheet = workbook.add_worksheet("Données comptages")
        sheet.protect(password=PASSWORD)
        sheet.set_zoom(85)
        sheet.set_tab_color("orange")
        sheet.set_column("A:A", 30)
        sheet.set_column("B:H", 15)
        x = 1
        for affaire in self.env['production.affaire'].search(search_ids, order='name desc'):
            sheet.merge_range("A" + str(x) + ':G' + str(x), affaire.full_name, style_title)
            x = x + 1
            sheet.write("A" + str(x), "Modèle", style_title)
            sheet.write("B" + str(x), "PREV", style_title)
            sheet.write("C" + str(x), "EXE", style_title)
            sheet.write("D" + str(x), "IND", style_title)
            sheet.write("E" + str(x), "%", style_title)
            sheet.write("F" + str(x), "H.INGENIEURS", style_title)
            sheet.write("G" + str(x), "H.PROJETEURS", style_title)
            x = x + 1
            self._cr.execute(f"""SELECT 
                                    pdt.name,
                                    CASE WHEN t3.prev IS NULL THEN 0 ELSE t3.prev END AS prev,
                                    CASE WHEN t3.exe IS NULL THEN 0 ELSE t3.exe END AS exe,
                                    CASE WHEN t3.indice IS NULL THEN 0 ELSE t3.indice END AS indice,
                                    CASE WHEN t3.exe IS NULL OR t3.prev = 0 OR t3.exe = 0 THEN 0 ELSE ROUND(1.00 * t3.exe / t3.prev, 2) END AS exe_to_prev_ratio,
                                    CASE WHEN t2.nb_hour_ing IS NULL THEN 0 ELSE t2.nb_hour_ing END AS nb_hour_ing,
                                    CASE WHEN t2.nb_hour_proj IS NULL THEN 0 ELSE t2.nb_hour_proj END AS nb_hour_proj
                                FROM 
                                    production_document_type pdt
                                LEFT JOIN (
                                    SELECT 
                                        COALESCE(t1.type_id, t2.type_id) AS type_id, prev, exe, indice
                                    FROM (
                                        SELECT affaire_id, type_id, prev 
                                        FROM production_affaire_document_type
                                        WHERE affaire_id = {affaire.id}
                                    ) AS t1
                                    FULL OUTER JOIN (
                                        SELECT affaire_id, type_id, COUNT(DISTINCT pd.id) AS exe, COUNT(DISTINCT pdi.id) AS indice 
                                        FROM production_document pd
                                        INNER JOIN production_document_indice pdi ON pd.id = pdi.document_id
                                        WHERE affaire_id = {affaire.id}
                                        GROUP BY affaire_id, type_id
                                    ) AS t2 
                                    ON t1.type_id = t2.type_id
                                ) AS t3 
                                ON t3.type_id = pdt.id
                                LEFT JOIN (
                                    SELECT 
                                        pd.type_id, t1.affaire_id, t1.document_id, t1.nb_hour_ing, t1.nb_hour_proj
                                    FROM production_document pd
                                    INNER JOIN (
                                        SELECT 
                                            b.affaire_id,
                                            b.document_id,
                                            a.employee_id,
                                            SUM(CASE WHEN job.name LIKE 'Ing%' THEN b.hour ELSE 0 END) AS nb_hour_ing,
                                            SUM(CASE WHEN job.name LIKE 'Proj%' THEN b.hour ELSE 0 END) AS nb_hour_proj
                                        FROM production_pointage a
                                        INNER JOIN production_pointage_line b ON a.id = b.pointage_id
                                        INNER JOIN production_employee emp ON emp.id = a.employee_id
                                        INNER JOIN production_job job ON job.id = emp.job_id
                                        WHERE b.type LIKE 'document' AND a.state = 'sent' AND b.affaire_id = {affaire.id}
                                        GROUP BY b.affaire_id, b.document_id, a.employee_id
                                    ) AS t1 ON t1.document_id = pd.id
                                ) AS t2 ON t2.type_id = pdt.id
                                ORDER BY pdt.sequence""")
            for row in self._cr.fetchall():
                if row[1] > row[2]:
                    _style = style_green
                    _style_number = style_number_green
                    _style_percentage = style_percentage_green
                elif row[1] < row[2]:
                    _style = style_red
                    _style_number = style_number_red
                    _style_percentage = style_percentage_red
                else:
                    _style = style_orange
                    _style_number = style_number_orange
                    _style_percentage = style_percentage_orange
                sheet.write("A" + str(x), row[0], _style)
                sheet.write("B" + str(x), row[1], _style)
                sheet.write("C" + str(x), row[2], _style)
                sheet.write("D" + str(x), row[3], _style)
                sheet.write("E" + str(x), row[4], _style_percentage)
                sheet.write("F" + str(x), row[5], _style_number)
                sheet.write("G" + str(x), row[6], _style_number)
                x = x + 1
            x  = x + 1
            sheet.merge_range("A" + str(x) + ':E' + str(x), "Modèle", style_title)
            sheet.write("F" + str(x), "H.INGENIEURS", style_title)
            sheet.write("G" + str(x), "H.PROJETEURS", style_title)
            x = x + 1
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
            								order by r.sequence""".format(affaire.id))
            for row in self._cr.fetchall():
                sheet.merge_range("A" + str(x) + ':E' + str(x), row[0], style)
                sheet.write("F" + str(x), row[1], style_number)
                sheet.write("G" + str(x), row[2], style_number)
                x = x + 1


            for (pointage_type, pointage_name) in [('modelisation_cao', 'Modélisation CAO'),
                                                   ('modelisation_calcul', 'Modélisation Calcul'),
                                                   ('research', 'Recherche'),
                                                   ('stand', 'Stand by'),
                                                   ('other', 'Autre')]:
                self._cr.execute(f""" select '{pointage_name}',
                                        sum(case when job.name like 'Ing%' then b.hour else 0 end) as nb_hour_ing,
                                        sum(case when job.name like 'Proj%' then b.hour else 0 end) as nb_hour_proj 
                                    from production_pointage a
                                    inner join production_pointage_line b on a.id=b.pointage_id
                                    inner join production_employee emp on emp.id=a.employee_id
                                    inner join production_job job on job.id=emp.job_id
                                    where b.type like '{pointage_type}'
                                    and a.state = 'sent'
                                    and b.affaire_id={affaire.id}
                                    group by b.affaire_id,b.document_id,a.employee_id""")
                row = self._cr.fetchone()
                sheet.merge_range("A" + str(x) + ':E' + str(x), pointage_name, style)
                if row:
                    sheet.write("F" + str(x), row[1], style_number)
                    sheet.write("G" + str(x), row[2], style_number)
                else:
                    sheet.write("F" + str(x), 0, style_number)
                    sheet.write("G" + str(x), 0, style_number)
                x = x + 1
        workbook.close()

        return self.get_return(filename)

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

    def action_print_report_prod(self):
        # Vérifier si l'affaire est définie
        if not self.affaire_id:
            raise UserError('Veuillez sélectionner une affaire pour générer le rapport.')

        docs = self.env['res.company'].browse(self.env.company.id)
        # Collecter les données nécessaires pour le rapport
        data = {
            'affaire_name': self.affaire_id.full_name,
            'date': datetime.datetime.today().strftime('%d-%m-%Y'),
            'docs': self.env['res.company'].browse(self.env.company.id),
            'doc_model': 'production.report',
            'documents': [],
            'times': []
        }
        self._cr.execute(f"""SELECT 
                                pdt.name,
                                t3.prev AS prev,
                                t3.exe AS exe,
                                t3.indice AS indice,
                                CASE WHEN t3.exe IS NULL OR t3.prev IS NULL OR t3.prev = 0 OR t3.exe = 0 THEN 0 ELSE ROUND(1.00 * t3.exe / t3.prev, 2) * 100 END AS exe_to_prev_ratio,
                                SUM(CASE WHEN t2.nb_hour_ing IS NULL THEN 0 ELSE t2.nb_hour_ing END) AS nb_hour_ing,
                                SUM(CASE WHEN t2.nb_hour_proj IS NULL THEN 0 ELSE t2.nb_hour_proj END) AS nb_hour_proj
                            FROM 
                                production_document_type pdt
                            LEFT JOIN (
                                SELECT 
                                    COALESCE(t1.type_id, t2.type_id) AS type_id, 
									CASE WHEN prev IS NULL THEN 0 ELSE prev END as prev, 
									CASE WHEN exe IS NULL THEN 0 ELSE exe END as exe, 
									CASE WHEN indice IS NULL THEN 0 ELSE indice END as indice
                                FROM (
                                    SELECT affaire_id, type_id, prev 
                                    FROM production_affaire_document_type
                                    WHERE affaire_id = {self.affaire_id.id}
                                ) AS t1
                                FULL OUTER JOIN (
                                    SELECT affaire_id, type_id, COUNT(DISTINCT pd.id) AS exe, COUNT(DISTINCT pdi.id) AS indice 
                                    FROM production_document pd
                                    INNER JOIN production_document_indice pdi ON pd.id = pdi.document_id
                                    WHERE affaire_id = {self.affaire_id.id}
                                    GROUP BY affaire_id, type_id
                                ) AS t2 
                                ON t1.type_id = t2.type_id
                            ) AS t3 
                            ON t3.type_id = pdt.id
                            LEFT JOIN (
                                SELECT 
                                    pd.type_id, t1.affaire_id, t1.document_id, t1.nb_hour_ing, t1.nb_hour_proj
                                FROM production_document pd
                                INNER JOIN (
                                    SELECT 
                                        b.affaire_id,
                                        b.document_id,
                                        a.employee_id,
                                        SUM(CASE WHEN job.name LIKE 'Ing%' THEN b.hour ELSE 0 END) AS nb_hour_ing,
                                        SUM(CASE WHEN job.name LIKE 'Proj%' THEN b.hour ELSE 0 END) AS nb_hour_proj
                                    FROM production_pointage a
                                    INNER JOIN production_pointage_line b ON a.id = b.pointage_id
                                    INNER JOIN production_employee emp ON emp.id = a.employee_id
                                    INNER JOIN production_job job ON job.id = emp.job_id
                                    WHERE b.type LIKE 'document' AND a.state = 'sent' 
                                    AND b.affaire_id = {self.affaire_id.id}
                                    GROUP BY b.affaire_id, b.document_id, a.employee_id
                                ) AS t1 ON t1.document_id = pd.id
                            ) AS t2 ON t2.type_id = pdt.id
							GROUP BY pdt.name, pdt.sequence, t3.prev, t3.exe, t3.indice
                            ORDER BY pdt.sequence""")
        for row in self._cr.fetchall():
            data['documents'].append({
                'name': row[0],
                'prev': row[1],
                'exe': row[2],
                'indice': row[3],
                'percentage': row[4],
                'hours_ing': row[5],
                'hours_proj': row[6]
            })

        self._cr.execute(f"""select r.name,case when t2.nb_hour_ing is null then 0 else t2.nb_hour_ing end,
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
                                                    and b.affaire_id = {self.affaire_id.id}
                                                    group by b.affaire_id,b.reunion_id,a.employee_id) as t2
                                                    on t2.reunion_id = r.id
                    								order by r.sequence""")
        for row in self._cr.fetchall():
            data['times'].append({
                'name': row[0],
                'hours_ing': row[1],
                'hours_proj': row[2]
            })

        for (pointage_type, pointage_name) in [('modelisation_cao', 'Modélisation CAO'),
                                               ('modelisation_calcul', 'Modélisation Calcul'),
                                               ('research', 'Recherche'),
                                               ('stand', 'Stand by'),
                                               ('other', 'Autre')]:
            self._cr.execute(f""" select '{pointage_name}',
                                                sum(case when job.name like 'Ing%' then b.hour else 0 end) as nb_hour_ing,
                                                sum(case when job.name like 'Proj%' then b.hour else 0 end) as nb_hour_proj 
                                            from production_pointage a
                                            inner join production_pointage_line b on a.id=b.pointage_id
                                            inner join production_employee emp on emp.id=a.employee_id
                                            inner join production_job job on job.id=emp.job_id
                                            where b.type like '{pointage_type}'
                                            and a.state = 'sent'
                                            and b.affaire_id = {self.affaire_id.id}
                                            group by b.affaire_id,b.document_id,a.employee_id""")
            row = self._cr.fetchone()
            if row:
                data['times'].append({
                    'name': pointage_name,
                    'hours_ing': row[1],
                    'hours_proj': row[2]
                })
            else:
                data['times'].append({
                    'name': pointage_name,
                    'hours_ing': 0,
                    'hours_proj': 0
                })
        return self.env.ref('tectone.action_report_production_html').report_action(self, data=data)

    def action_print_report_fin(self):
        # Vérifier si l'affaire est définie
        if not self.affaire_id:
            raise UserError('Veuillez sélectionner une affaire pour générer le rapport.')

        docs = self.env['res.company'].browse(self.env.company.id)

        data = {
            'affaire_name': self.affaire_id.full_name,
            'date': datetime.datetime.today().strftime('%d-%m-%Y'),
            'docs': self.env['res.company'].browse(self.env.company.id),
            'doc_model': 'production.report',
            'amount_contract': self.affaire_id.amount_contract,
            'amount_avenant': self.affaire_id.amount_avenant,
            'amount_billed': self.affaire_id.amount_billed,
            'amount_payed': self.affaire_id.amount_payed,
            'percentage_billed': self.affaire_id.percentage_billed,
            'percentage_payed': self.affaire_id.percentage_payed,
            'currency': self.affaire_id.currency_id.symbol
        }

        return self.env.ref('tectone.action_report_finance_html').report_action(self, data=data)

class ProductionPrintReport(models.AbstractModel):
    _name = 'report.tectone.report_production_print'
    _description = "Production Report Print"

    @api.model
    def _get_report_values(self, docids, data=None):
        print('data')
        print(data)

        return {
            'doc_ids': docids,
            'doc_model': 'production.report.print',
            'docs': self.env['res.company'].browse(self.env.company.id),
        }