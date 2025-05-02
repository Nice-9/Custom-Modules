
from odoo import api, fields, models, _

class HrSalaryRuleCategory(models.Model):
    _inherit = 'hr.salary.rule.category'

    payslip_section = fields.Selection(selection=[
            ('Basic', "Basic"),
            ('Allowance', "Allowance"),
            ('Deduction', "Deduction"),
            ('Gross', "Gross"),
            ('Net', "Net"),
        ],string="Payslip Section")


class HrPayslipLine(models.Model):
    _inherit = 'hr.payslip.line'

    category_section = fields.Selection(selection=[
            ('Basic', "Basic"),
            ('Allowance', "Allowance"),
            ('Deduction', "Deduction"),
            ('Gross', "Gross"),
            ('Net', "Net"),
        ],string="Payslip Section",related="category_id.payslip_section")