from odoo import api, fields, models, _
from odoo.exceptions import ValidationError, UserError


class LoanClosureReason(models.Model):
    """ Model for managing loan requests."""
    _name = 'loan.closure.reason'
    _description = "Loan Closure Reason"

    name = fields.Char("Name",required=True)