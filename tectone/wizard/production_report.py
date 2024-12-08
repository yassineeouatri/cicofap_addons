import os
import time
import xlsxwriter
from odoo import models, fields, api, _
from odoo.exceptions import UserError

PASSWORD = "cestsecret"
LOCAL_DIRECTORY = "C://Program Files//Odoo15//server//odoo//addons//web//static//reports//"
#LOCAL_DIRECTORY = "C://Users//Yassine//PycharmProjects//cicofap//Scripts//odoo//addons//web//static//reporting//"

class ProductionReport(models.TransientModel):
    _name = "production.report"
    _description = "Generate report"

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
        sheet.set_column("A:A", 100)
        sheet.set_column("B:G", 15)
        x = 1
        sheet.write("A" + str(x), "Affaire", style_title)
        sheet.write("B" + str(x), "Montant contrat", style_title)
        sheet.write("C" + str(x), "Montant avenant", style_title)
        sheet.write("D" + str(x), "Montant facturé", style_title)
        sheet.write("E" + str(x), "Montant payé", style_title)
        sheet.write("F" + str(x), "% facturé", style_title)
        sheet.write("G" + str(x), "% payé", style_title)
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
            sheet.write("A" + str(x), affaire.full_name, style)
            sheet.write("B" + str(x), affaire.amount_contract, style_number)
            sheet.write("C" + str(x), affaire.amount_avenant, style_number)
            sheet.write("D" + str(x), affaire.amount_billed, style_number)
            sheet.write("E" + str(x), affaire.amount_payed, style_number)
            sheet.write("F" + str(x), affaire.percentage_billed, style_percentage)
            sheet.write("G" + str(x), affaire.percentage_payed, style_percentage)
            x = x + 1
        workbook.close()

        return self.get_return(filename)

    def action_print_report_prod(self):
        if self.affaire_id:
            filename = "Rapport production - " + str(self.affaire_id.number)+ " - "+ time.strftime("%H%M%S") + ".xlsx"
            search_ids = [('id', '=', self.affaire_id.id)]
        else:
            filename = "Rapport production - " + time.strftime("%H%M%S") + ".xlsx"
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
        sheet = workbook.add_worksheet("Données comptages")
        sheet.protect(password=PASSWORD)
        sheet.set_zoom(85)
        sheet.set_tab_color("orange")
        sheet.set_column("A:A", 100)
        sheet.set_column("B:H", 15)
        x = 1
        sheet.write("A" + str(x), "Affaire", style_title)
        sheet.write("B" + str(x), "Modèle", style_title)
        sheet.write("C" + str(x), "PREV", style_title)
        sheet.write("D" + str(x), "EXE", style_title)
        sheet.write("E" + str(x), "IND", style_title)
        sheet.write("F" + str(x), "%", style_title)
        sheet.write("G" + str(x), "H.INGENIEURS", style_title)
        sheet.write("H" + str(x), "H.PROJETEURS", style_title)
        x += 1
        for affaire in self.env['production.affaire'].search(search_ids, order='name desc'):
            x_deb = x
            self._cr.execute("""select pdt.name,
                                            case when t3.prev is null then 0 else t3.prev end as prev,
                                            case when t3.exe is null then 0 else t3.exe end as exe,
                                            case when t3.indice is null then 0 else t3.indice end as indice,
                                            case when t3.exe is null or t3.prev=0 or t3.exe=0 then 0 else round(1.00 * t3.exe/t3.prev) end
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
                                            order by pdt.sequence""".format(affaire.id, affaire.id))
            for row in self._cr.fetchall():
                sheet.write("A" + str(x), affaire.full_name, style)
                sheet.write("B" + str(x), row[0], style)
                sheet.write("C" + str(x), row[1], style)
                sheet.write("D" + str(x), row[2], style)
                sheet.write("E" + str(x), row[3], style)
                sheet.write("F" + str(x), row[4], style_percentage)
                x += 1
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
                                            order by pdt.sequence""".format(affaire.id))
            for row in self._cr.fetchall():
                sheet.write("G" + str(x_deb), row[1], style_number)
                sheet.write("H" + str(x_deb), row[2], style_number)
                x_deb += 1

            self._cr.execute("""select name,0,0,0,0 from production_reunion order by sequence""")
            for row in self._cr.fetchall():
                sheet.write("A" + str(x), affaire.full_name, style)
                sheet.write("B" + str(x), row[0], style)
                sheet.write("C" + str(x), row[1], style)
                sheet.write("D" + str(x), row[2], style)
                sheet.write("E" + str(x), row[3], style)
                sheet.write("F" + str(x), row[4], style_percentage)
                x += 1
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
                sheet.write("G" + str(x_deb), row[1], style_number)
                sheet.write("H" + str(x_deb), row[2], style_number)
                x_deb += 1

            for model in ['Recherche', 'Stand by', 'Autre']:
                sheet.write("A" + str(x), affaire.full_name, style)
                sheet.write("B" + str(x), model, style)
                sheet.write("C" + str(x), 0, style)
                sheet.write("D" + str(x), 0, style)
                sheet.write("E" + str(x), 0, style)
                sheet.write("F" + str(x), 0, style_percentage)
                x += 1
            for model in ['research', 'stand', 'other']:
                self._cr.execute(""" select 'Recherche',
                                        sum(case when job.name like 'Ing%' then b.hour else 0 end) as nb_hour_ing,
                                        sum(case when job.name like 'Proj%' then b.hour else 0 end) as nb_hour_proj 
                                    from production_pointage a
                                    inner join production_pointage_line b on a.id=b.pointage_id
                                    inner join production_employee emp on emp.id=a.employee_id
                                    inner join production_job job on job.id=emp.job_id
                                    where b.type like 'research'
                                    and a.state = '{}'
                                    and b.affaire_id={}
                                    group by b.affaire_id,b.document_id,a.employee_id""".format(model, affaire.id))
                row = self._cr.fetchone()
                if row:
                    sheet.write("G" + str(x_deb), row[1], style_number)
                    sheet.write("H" + str(x_deb), row[2], style_number)
                    x_deb += 1
                else:
                    sheet.write("G" + str(x_deb), 0, style_number)
                    sheet.write("H" + str(x_deb), 0, style_number)
                    x_deb += 1
        workbook.close()

        return self.get_return(filename)


    def get_return(self, fichier):
        url = "/web/static/reports/" + fichier
        if url:
            return {
                "type": "ir.actions.act_url",
                "target": "new",
                "url": url,
                "nodestroy": True,
            }
        else:
            return True

