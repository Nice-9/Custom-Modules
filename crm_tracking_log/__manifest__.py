{
    'name': 'CRM Lead Tracking Log',
    'version': '1.0',
    'category': 'CRM',
    'summary': 'Track salesperson locations and link to CRM leads',
    'depends': ['crm'],
    'data': [
        'security/ir.model.access.csv',
        'security/security.xml',
        'views/tracking_log_views.xml',
        'views/tracking_log_dashboard.xml',
        'data/tracking_log_dashboard_data.xml',
    ],
    'installable': True,
    'application': True,
}
