{
    'name': 'Fleet Fuel Custom',
    'version': '1.0',
    'summary': 'Fuel estimation, trip logs, and reporting for Odoo Fleet',
    'author': 'Dibon',
    'depends': ['fleet', 'report_xlsx'],
    'data': [
        'security/ir.model.access.csv',
        'views/fleet_vehicle_log_fuel_views.xml',
        'views/fleet_vehicle_trip_views.xml',
        'views/fleet_fuel_export_wizard_view.xml',
        'reports/fleet_fuel_report_pdf.xml',
        'reports/fleet_fuel_log_pdf_template.xml',
        'reports/fleet_fuel_report_xlsx.xml',
    ],
    'installable': True,
    'application': True,
}
