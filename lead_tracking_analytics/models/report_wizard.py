from odoo import models, fields
from datetime import datetime

class TrackingLogReportWizard(models.TransientModel):
    _name = 'report.tracking.log.wizard'
    _description = 'Tracking Log Report Wizard'

    start_date = fields.Datetime("Start Date", required=True)
    end_date = fields.Datetime("End Date", required=True)
    report_format = fields.Selection([
        ('pdf', 'PDF'),
        ('excel', 'Excel')
    ], string="Format", required=True)

    def action_generate_report(self):
        self.ensure_one()
        data = {
            'start_date': self.start_date.strftime('%Y-%m-%d %H:%M:%S'),
            'end_date': self.end_date.strftime('%Y-%m-%d %H:%M:%S'),
        }
        if self.report_format == 'pdf':
            return self.env.ref('crm_lead_tracking_analytics.action_tracking_log_pdf').report_action(self, data=data)
        else:
            return {
                'type': 'ir.actions.act_url',
                'url': f'/tracking/log/report/excel?start={data["start_date"]}&end={data["end_date"]}',
                'target': 'self',
            }
