# -*- coding: utf-8 -*-
{
    "name": "Sybyl Payslip Report",
    "summary": """ HR Payslip report with column based listing of salary rules where Basic, Allowances and Gross salary rules are displayed on the left side and Deductions and Net Pay are displayed on the right side.""",
    "author": "Sybyl",
    "website": "https://sybyl.com",
    "version": "17.0.0.0",
    "depends": [
        "hr_payroll",
    ],
    "data": ["views/salary_rule_category_view.xml"],
    "assets": {
    },
    "application": True,
    "license": "LGPL-3",
}
