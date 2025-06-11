from odoo import api, fields, models

class MPesaSMSConfig(models.Model):
    _inherit = 'mpesa.sms.config'

    current_balance = fields.Float('Current Balance', readonly=True)
    total_sent = fields.Integer('Total SMS Sent', compute='_compute_stats')
    success_count = fields.Integer('Successful SMS', compute='_compute_stats')
    failed_count = fields.Integer('Failed SMS', compute='_compute_stats')
    success_rate = fields.Float('Success Rate (%)', compute='_compute_stats')
    
    def _compute_stats(self):
        for record in self:
            domain = [('sender_id', '=', record.id)]
            record.total_sent = self.env['mpesa.sms.log'].search_count(domain)
            record.success_count = self.env['mpesa.sms.log'].search_count(domain + [('status', '=', 'success')])
            record.failed_count = self.env['mpesa.sms.log'].search_count(domain + [('status', '=', 'failed')])
            record.success_rate = (record.success_count / record.total_sent * 100) if record.total_sent else 0

    def update_balance(self, new_balance):
        self.current_balance = float(new_balance.replace('KES ', ''))
