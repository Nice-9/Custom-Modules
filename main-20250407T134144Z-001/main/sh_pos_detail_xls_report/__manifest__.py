# -*- coding: utf-8 -*-
# Part of Softhealer Technologies.
{
    "name": "Point Of Sale Excel Reports",
    "author": "Softhealer Technologies",
    "website": "https://www.softhealer.com",
    "support": "support@softhealer.com",
    "license": "OPL-1",
    "category": "Point Of Sale",
    "summary": "Merge Excel Report Of Point Of Sales Order Generate Point Of Sale Order Excel Report Mass Excel Report Bulk Point Of Sale Excel Report POS Excel Report Print Excel Report Point Of Sale XLS Report POS XLS Report Point Of Sale Order XLS Odoo Point Of Sale Detail XLS Report Point Of Sale Order Excel Reports POS Excel Reports POS Order Excel Report",
    "description":  """If you want to get excel reports of POS orders. So here we build a module that can help to print the excel report of the POS orders. You can get an excel report separate sheet of each order also. Cheers!""",
    "version": "0.0.1",
    "depends": ["point_of_sale"],
    "application": True,
    "data": [
        "views/pos_sale_details.xml",
        "wizard/pos_detail_wizard_views.xml",
    ],
    "auto_install": False,
    "installable": True,
    "images": ["static/description/background.png", ],
    "price": 15,
    "currency": "EUR"
}
