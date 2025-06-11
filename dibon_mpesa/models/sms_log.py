import logging
from odoo import api, fields, models

_logger = logging.getLogger(__name__)

class SMSLog(models.Model):
    _name = 'mpesa.sms.log'
    _description = 'SMS Log'
    _order = 'create_date desc'

    name = fields.Char('Message ID')
    sender_id = fields.Many2one('mpesa.sms.config', string='Sender ID', 
                                ondelete='cascade', required=True)
    recipient = fields.Char('Recipient')
    message = fields.Text('Message')
    status = fields.Selection([
        ('success', 'Success'),
        ('failed', 'Failed')
    ], string='Status', default='success')
    cost = fields.Float('Cost')
    reference = fields.Char('Reference')
    transaction_id = fields.Many2one('payment.transaction', string='Transaction')

    @api.model_create_multi
    def create(self, vals_list):
        """Override create to support batch creation"""
        _logger.info("SMS_LOG: Creating %d log entries", len(vals_list))
        records = super().create(vals_list)
        _logger.info("SMS_LOG: Successfully created %d log entries", len(records))
        return records
