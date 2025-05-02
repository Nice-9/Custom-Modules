from odoo import models, fields, api
from odoo.tools import format_date
from datetime import datetime, date


class FleetOdometerReportWizard(models.TransientModel):
    _name = 'fleet.odometer.report.wizard'
    _description = 'Fleet Odometer Report Wizard'

    start_date = fields.Date(string='Start Date', required=True, default=lambda self: date.today().replace(day=1))
    end_date = fields.Date(string='End Date', required=True, default=lambda self: date.today())
    driver_id = fields.Many2one('res.partner', string="Driver")
    vehicle_id = fields.Many2one('fleet.vehicle', string="Vehicle")

    def action_generate_report(self):
        return self.env.ref('sybyl_fleet_report.action_fleet_odometer_report').report_action(self)
        
    def get_data(self):
        domain = [('date', '>=', self.start_date), ('date', '<=', self.end_date)]
        if self.driver_id:
            domain.append(('driver_id', '=', self.driver_id.id))
        if self.vehicle_id:
            domain.append(('vehicle_id', '=', self.vehicle_id.id))

        odometer_records = self.env['fleet.vehicle.odometer'].search(domain, order='date asc')

        grouped_records = {}
        for record in odometer_records:
            vehicle = record.vehicle_id
            if vehicle not in grouped_records:
                grouped_records[vehicle] = []
            grouped_records[vehicle].append(record)

        # grouped_data = {}
        # for record in odometer_records:
        #     month_key = record.date.strftime('%Y-%m')
        #     if month_key not in grouped_data:
        #         grouped_data[month_key] = []
        #     grouped_data[month_key].append(record)

        # Calculate differences for each vehicle
        differences = []
        for vehicle, records in grouped_records.items():
            previous_record = None
            for record in records:
                if previous_record:
                    differences.append({
                        'vehicle_name': vehicle.name,
                        'driver_name': record.driver_id.name,
                        'previous_date': previous_record.date,
                        'current_date': record.date,
                        'previous_value': previous_record.value,
                        'current_value': record.value,
                        'difference': round(record.value - previous_record.value,2),
                        'month_key': record.date.strftime('%B %Y'),
                    })
                previous_record = record

        month_keys = list(set(record['month_key'] for record in differences))
        grouped_records = {month: [] for month in month_keys}
        for record in differences:
            grouped_records[record['month_key']].append(record)
        months = list(grouped_records.keys())
        months_values = list(grouped_records.values())


        return [months, months_values]

    def get_com_data(self):
        user_lang = self.env.user.lang or 'en_US'
        start_date_formatted = format_date(self.env, self.start_date, lang_code=user_lang)
        end_date_formatted = format_date(self.env, self.end_date, lang_code=user_lang)
        print_time = datetime.now()
        lang_obj = self.env['res.lang'].search([('code', '=', user_lang)], limit=1)
        date_format = lang_obj.date_format or '%Y-%m-%d'
        time_format = lang_obj.time_format or '%H:%M:%S'
        return {
            "sdate": start_date_formatted,
            "edate": end_date_formatted,
            "ptime": print_time.strftime(f"{date_format} {time_format}"),
            "pby": self.env.user.name,
            'driver': self.driver_id.name if self.driver_id else '-',
            'vehicle': self.vehicle_id.name if self.vehicle_id else '-'
        }

