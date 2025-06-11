# -*- coding: utf-8 -*-

from odoo import models, fields


class MpesaLog(models.Model):
    _name = 'mpesa.log'
    _description = 'MPesa Transaction Logs'
    _order = 'create_date desc'

    name = fields.Text('Request Payload')
    status_code = fields.Integer('Response Status Code')
    response = fields.Text('Response')
    checkout_request_id = fields.Char('Checkout Request ID')
    payment_transaction_id = fields.Many2one('payment.transaction', 'Payment Transaction')
    result_code = fields.Char('Result Code')
    response_error = fields.Text('Error Message')
