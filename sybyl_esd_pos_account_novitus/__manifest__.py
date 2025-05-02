# -*- coding: utf-8 -*-
{
    "name": "Sybyl ESD POS & Account Novitus",
    "summary": """Sybyl ESD POS & Account Novitus""",
    "author": "Sybyl",
    "website": "https://www.sybylcloud.com",
    "category": "Uncategorized",
    "version": "17.0.0.3",
    "sequence": 1,
    "license": "LGPL-3",
    "external_dependencies": {
        "python": [
            "xmltodict",
            "pyqrcode",
            "pypng",
        ]
    },
    "depends": [
        "account",
        "l10n_ke",
        "point_of_sale",
        "pos_loyalty",
        "pos_discount",
        "sybyl_karura_pos",
        "sale"
    ],
    "data": [
        "data/ir_cron_data.xml",
        "security/ir.model.access.csv",
        "security/security.xml",
        "views/res_partner_view.xml",
        "views/res_partner_bank.xml",
        "views/res_company_views.xml",
        "views/res_config_settings_views.xml",
        "views/account_payment_method_views.xml",
        "views/account_tax_views.xml",
        "views/account_fiscal_log_view.xml",
        "views/account_move_views.xml",
        "views/product_template_views.xml",
        "report/report_invoice_templates.xml",
        "views/pos_payment_method_views.xml",
        "views/pos_order_views.xml",
        "views/pos_config_views.xml",
        "views/fiscal_log_view.xml",
    ],
    "assets": {
        "point_of_sale.assets": [
            # 'sybyl_pos_fiscal_printer/static/src/js/fiscal_printers.js',
            "sybyl_esd_pos_account_novitus/static/src/js/models.js",
            "sybyl_esd_pos_account_novitus/static/src/js/pos_fiscal_printer.js",
            "sybyl_esd_pos_account_novitus/static/src/js/PaymentScreen.js",
            "sybyl_esd_pos_account_novitus/static/src/js/TicketScreen.js",
        ],
        "web.assets_qweb": [
            "sybyl_esd_pos_account_novitus/static/src/xml/**/*",
            # 'sybyl_esd_pos_account_novitus/static/src/xml/order_receiept_extended.xml',
        ],
        "point_of_sale._assets_pos": [
            "sybyl_esd_pos_account_novitus/static/src/js/order_receipt_extended.js",
            "sybyl_esd_pos_account_novitus/static/src/xml/order_receiept_extended.xml",
        ],
    },
    "application": True,
}
