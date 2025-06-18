from odoo import models
from collections import defaultdict

class FuelLogXlsxReport(models.AbstractModel):
    _name = 'report.fleet_fuel_custom.report_fuel_log_xlsx'
    _inherit = 'report.report_xlsx.abstract'

    def generate_xlsx_report(self, workbook, data, logs):
        sheet_format = workbook.add_format({'bold': True})
        logs_by_vehicle = defaultdict(list)

        for log in logs:
            vehicle = log.vehicle_id.name or "Unknown Vehicle"
            logs_by_vehicle[vehicle].append(log)

        multi_vehicle = len(logs_by_vehicle) > 1
        totals = {'est': 0.0, 'act': 0.0, 'var': 0.0, 'cost': 0.0}

        for vehicle, records in logs_by_vehicle.items():
            sheet = workbook.add_worksheet(vehicle[:31])
            headers = [
                'Date', 'Driver', 'Trip', 'Estimated Litres', 'Actual Litres',
                'Variance', 'Cost/Litre', 'Estimated Cost'
            ]
            for col, title in enumerate(headers):
                sheet.write(0, col, title, sheet_format)

            for row, log in enumerate(records, start=1):
                sheet.write(row, 0, str(log.date))
                sheet.write(row, 1, log.driver_id.name if log.driver_id else '')
                sheet.write(row, 2, log.trip_id.name if log.trip_id else '')
                sheet.write(row, 3, log.litres_estimated)
                sheet.write(row, 4, log.liter)
                sheet.write(row, 5, log.fuel_variance)
                sheet.write(row, 6, log.cost_per_litre)
                sheet.write(row, 7, log.total_cost_estimated)

                if multi_vehicle:
                    totals['est'] += log.litres_estimated or 0.0
                    totals['act'] += log.liter or 0.0
                    totals['var'] += log.fuel_variance or 0.0
                    totals['cost'] += log.total_cost_estimated or 0.0

        if multi_vehicle:
            summary = workbook.add_worksheet("Summary")
            summary.write('A1', 'Total Estimated Litres', sheet_format)
            summary.write('B1', totals['est'])
            summary.write('A2', 'Total Actual Litres', sheet_format)
            summary.write('B2', totals['act'])
            summary.write('A3', 'Total Variance', sheet_format)
            summary.write('B3', totals['var'])
            summary.write('A4', 'Total Estimated Cost', sheet_format)
            summary.write('B4', totals['cost'])
