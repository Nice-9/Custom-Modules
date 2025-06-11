from odoo import api, fields, models
import logging

_logger = logging.getLogger(__name__)

class MPesaSMSConfig(models.Model):
    _name = 'mpesa.sms.config'
    _description = 'Mpesa SMS Configuration'

    name = fields.Char('Name', required=True)
    is_enabled = fields.Boolean('Enable SMS Notifications', default=False)
    endpoint = fields.Char('SMS API Endpoint', default='http://sms.dibon.co.ke:8989/api/messaging/sendsms')
    api_key = fields.Char('API Key', required_if_enabled=True)
    sender_id = fields.Char('Sender ID', required_if_enabled=True)
    sms_template = fields.Text(
        'SMS Template',
        default='Dear Customer,\nYour Transaction Confirmed!\nAmount: KES {amount}\nMpesa Receipt: {mpesa_ref}\nReference: {purchase_id}\nThank you for shopping with us.'
    )
    current_balance = fields.Float('Current Balance', readonly=True, default=0.0)
    total_sent = fields.Integer('Total SMS Sent', compute='_compute_stats', store=True)
    success_count = fields.Integer('Successful SMS', compute='_compute_stats', store=True)
    failed_count = fields.Integer('Failed SMS', compute='_compute_stats', store=True)
    success_rate = fields.Float('Success Rate (%)', compute='_compute_stats', store=True)

    # Add One2many relationship field
    sms_log_ids = fields.One2many('mpesa.sms.log', 'sender_id', string='SMS Logs')
    
    # Change depends to use correct field
    @api.depends('sms_log_ids.status')
    def _compute_stats(self):
        for record in self:
            _logger.info("Computing stats for config: %s", record.name)
            
            record.total_sent = len(record.sms_log_ids)
            record.success_count = len(record.sms_log_ids.filtered(lambda x: x.status == 'success'))
            record.failed_count = len(record.sms_log_ids.filtered(lambda x: x.status == 'failed'))
            record.success_rate = (record.success_count / record.total_sent * 100) if record.total_sent else 0.0
            
            _logger.info("Stats computed - Total: %s, Success: %s, Failed: %s, Rate: %s%%", 
                        record.total_sent, record.success_count, record.failed_count, record.success_rate)

    @api.model
    def create(self, vals):
        """Override create to log creation"""
        _logger.info("Creating new SMS config with values: %s", vals)
        return super().create(vals)

    def write(self, vals):
        """Override write to log updates"""
        _logger.info("Updating SMS config %s with values: %s", self.name, vals)
        return super().write(vals)

    def update_balance(self, new_balance):
        """Update sender balance from SMS response"""
        if new_balance:
            try:
                balance = float(new_balance.replace('KES ', ''))
                self.write({'current_balance': balance})
                _logger.info("Updated sender balance to: %s", balance)
            except (ValueError, AttributeError) as e:
                _logger.error("Failed to update balance: %s", str(e))
