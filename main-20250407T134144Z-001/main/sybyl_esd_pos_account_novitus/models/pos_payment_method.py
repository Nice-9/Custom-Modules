# -*- coding: utf-8 -*-
from odoo import fields, models


class PoSPaymentMethod(models.Model):
    _inherit = "pos.payment.method"

    fiscal_printer_payment_type = fields.Selection(
        [
            ("card", "Card"),
            ("cheque", "Cheque"),
            ("voucher", "Voucher"),
            ("credit", "Credit"),
            ("transfer", "Transfer"),
            ("customer_account", "Customer Account"),
            ("foreign_currency", "Foreign Currency"),
            ("cash", "Cash"),
            ("mobile", "Mobile"),
            ("token", "Token"),
        ],
        required=True,
        default="cash",
    )
