from odoo import models, fields

class FleetFuelExportWizard(models.TransientModel):
    _name = 'fleet.fuel.export.wizard'
    _description = 'Export Fuel Logs Wizard'

    start_date = fields.Datetime("Start Date", required=True)
    end_date = fields.Datetime("End Date", required=True)
    export_format = fields.Selection([('pdf', 'PDF'), ('xlsx', 'Excel')], default='xlsx', required=True)

    def export_logs(self):
        logs = self.env['fleet.vehicle.log.fuel'].search([
            ('date', '>=', self.start_date),
            ('date', '<=', self.end_date)
        ])
        if self.export_format == 'xlsx':
            return self.env.ref('fleet_fuel_custom.report_fuel_log_xlsx').report_action(logs)
        else:
            return self.env.ref('fleet_fuel_custom.report_fuel_log_pdf').report_action(logs)
