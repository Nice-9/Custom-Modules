{
    "name": "Tenant Rent",
    "version": "1.0",
    "summary": "Manage and report tenant rent payments",
    "depends": ["base", "account", "web", "report_xlsx"],
    "data": [
        "security/ir.model.access.csv",
        "views/tenant_views.xml",
        "reports/tenant_report_template.xml",
        "reports/tenant_report_action.xml"
    ],
    "installable": True,
    "application": True
}