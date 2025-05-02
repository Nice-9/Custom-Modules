from odoo import api, fields, models, _
from odoo.exceptions import ValidationError, UserError


class LoanType(models.Model):
    """ Model for managing loan requests."""
    _name = 'loan.type'
    _description = "Loan Type"

    name = fields.Char("Name",required=True)
    description = fields.Char("Description")