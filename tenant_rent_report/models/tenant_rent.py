from odoo import models, fields

class Tenant(models.Model):
    _name = 'tenant.rent'
    _description = 'Tenant Rent Payment'

    name = fields.Char(string="Tenant Name", required=True)
    rent_amount = fields.Float(string="Rent Amount", required=True)
    is_paid = fields.Boolean(string="Paid", default=False)