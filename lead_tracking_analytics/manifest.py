{
    'name': 'Lead Tracking Analytics',
    'version': '1.0',
    'author': 'Dibon',
    'depends': ['base', 'crm'],
    'category': 'Sales',
    'summary': 'Tracking analytics for CRM leads',
    'description': 'Adds graph views and PDF/Excel reports for CRM lead tracking logs.',
    'data': [
        'security/ir.model.access.csv',
        'views/tracking_log_graph.xml',
        'views/report_wizard_view.xml',
        'reports/tracking_log_pdf.xml',
    ],
    'application': True,
}
