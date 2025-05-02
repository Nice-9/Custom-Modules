
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class HrContract(models.Model):
    _inherit = 'hr.contract'

    l10n_ke_food_allowance = fields.Monetary("Transport Allowance")
    l10n_ke_pension_allowance = fields.Monetary("Special Allowance")
    l10n_ke_responsibility_allowance = fields.Monetary("Responsibility Alllowance")
