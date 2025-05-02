# -*- coding: utf-8 -*-
from odoo import fields, models


class AccountTax(models.Model):
    _inherit = "account.tax"

    fiscal_ptu_value = fields.Char("PTU Value", size=2, required=True, default="A")
    factor_type = fields.Selection(
        [("taxable", "Taxable"), ("exempted", "Exempted"), ("zero", "Zero Rated")],
        default="exempted",
        required=True,
    )
