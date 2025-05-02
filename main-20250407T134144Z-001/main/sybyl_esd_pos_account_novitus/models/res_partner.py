from odoo import models, fields


class ResPartner(models.Model):
    _inherit = "res.partner"

    is_vat_exempted = fields.Boolean(default=False)


class ResPartnerBank(models.Model):
    _inherit = 'res.partner.bank'

    # lipa_na_mpesa_type = fields.Selection()
    acc_number = fields.Char('Bank Account Number', required=True)
    lipa_na_mpesa_type = fields.Selection(
        selection=[
            ('paybill', 'Paybill'),
            ('buy_goods', 'Buy Goods'),
        ],
        string='Lipa na M-PESA',
    )
    paybill_till_num = fields.Char(string="PayBill / Till Number")
    account_number = fields.Char(string="Account Number")