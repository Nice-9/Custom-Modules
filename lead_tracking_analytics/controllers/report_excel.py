from odoo import http
from odoo.http import request
import io
import xlsxwriter
from datetime import datetime

class TrackingLogReportExcel(http.Controller):

    @http.route('/tracking/log/report/excel', type='http', auth='user')
    def export_excel(self, start=None, end=None, **kwargs):
        start_dt = datetime.strptime(start, '%Y-%m-%d %H:%M:%S')
        end_dt = datetime.strptime(end, '%Y-%m-%d %H:%M:%S')

        logs = request.env['crm.lead.tracking.log'].sudo().search([
            ('date', '>=', start_dt),
            ('date', '<=', end_dt),
        ])

        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output)
        sheet = workbook.add_worksheet("Tracking Logs")

        headers = ['Salesperson', 'Location', 'Date', 'Latitude', 'Longitude']
        for col, header in enumerate(headers):
            sheet.write(0, col, header)

        for row_num, log in enumerate(logs, start=1):
            sheet.write(row_num, 0, log.user_id.name)
            sheet.write(row_num, 1, log.name or "Offline")
            sheet.write(row_num, 2, str(log.date))
            sheet.write(row_num, 3, log.latitude)
            sheet.write(row_num, 4, log.longitude)

        workbook.close()
        output.seek(0)
        return request.make_response(
            output.read(),
            headers=[
                ('Content-Disposition', 'attachment; filename=tracking_logs.xlsx'),
                ('Content-Type', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
            ]
        )
