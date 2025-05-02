from odoo import models, fields, api

class FleetOdometerReportWizard(models.Model):
    _inherit = 'fleet.vehicle.odometer'

    def get_data(self, sdate, edate):
        odometer_records = self.env['fleet.vehicle.odometer'].search([
            ('date', '>=', sdate),
            ('date', '<=', edate)
        ], order='date asc')

        grouped_records = {}
        for record in odometer_records:
            vehicle = record.vehicle_id
            if vehicle not in grouped_records:
                grouped_records[vehicle] = []
            grouped_records[vehicle].append(record)

        # Calculate differences for each vehicle
        differences = []
        for vehicle, records in grouped_records.items():
            previous_record = None
            for record in records:
                if previous_record:
                    differences.append({
                        'vehicle_name': vehicle.name,
                        'previous_date': previous_record.date,
                        'current_date': record.date,
                        'previous_value': previous_record.value,
                        'current_value': record.value,
                        'difference': record.value - previous_record.value,
                    })
                previous_record = record
        return differences

