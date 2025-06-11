from odoo import models, fields, api

class MpesaSMSConfig(models.Model):
    _name = 'mpesa.sms.config'
    _description = 'Mpesa SMS Configuration'

    name = fields.Char(string='Name', required=True)
    is_enabled = fields.Boolean(string='Enable SMS Notifications', default=False)
    endpoint = fields.Char(string='SMS API Endpoint', default='http://sms.dibon.co.ke:8989/api/messaging/sendsms')
    api_key = fields.Char(string='API Key', required_if_enabled=True)
    sender_id = fields.Char(string='Sender ID', required_if_enabled=True)
    sms_template = fields.Text(
        string='SMS Template',
        default='''Dear Customer,
Your transaction of KES {amount} has been successful.
Mpesa Ref: {mpesa_ref}
Phone: {phone}
Purchase ID: {purchase_id}
Thank you for choosing us!''',
        help="Available variables: {amount}, {mpesa_ref}, {phone}, {purchase_id}"
    )

    @api.depends('is_enabled')
    def _compute_required_if_enabled(self):
        for record in self:
            record.required_if_enabled = record.is_enabled

    def format_message(self, transaction):
        """Format SMS message with transaction details"""
        return self.sms_template.format(
            amount=transaction.amount,
            mpesa_ref=transaction.mpesa_online_merchant_request_id,
            phone=transaction.partner_phone,
            purchase_id=transaction.reference
        )
