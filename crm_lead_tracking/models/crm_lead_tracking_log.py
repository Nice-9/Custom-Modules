import requests
from odoo import models, fields, api
from odoo.exceptions import UserError
from datetime import datetime, timedelta

class CrmLeadTrackingLog(models.Model):
    _name = 'crm.lead.tracking.log'
    _description = 'CRM Lead Tracking Log'
    _order = 'date desc'

    #name = fields.Char(string='Location Name')
    date = fields.Datetime(string='Date', default=fields.Datetime.now)
    user_id = fields.Many2one('res.users', string='Salesperson', default=lambda self: self.env.user)
    lead_id = fields.Many2one('crm.lead', string='CRM Lead')
    latitude = fields.Float(string='Latitude')
    longitude = fields.Float(string='Longitude')
    #status = fields.Selection([('success', 'Success'), ('failed', 'Failed')], string='Status', default='success')
    #error_message = fields.Text(string="Error", readonly=True)

    @api.model
    def create_tracking_log(self, lead):
        try:
            api_url = self.env['ir.config_parameter'].sudo().get_param('tracking.api.url')
            if not api_url:
                raise UserError("Tracking API URL or token not configured in system parameters.")
            response = requests.get(api_url, timeout=10)
            if response.status_code != 200:
                raise UserError(f"Tracking API error: {response.text}")
            data = response.json()
            self.create({
                #'name': data.get('location_name', 'Unknown'),
                'user_id': lead.user_id.id,
                'lead_id': lead.id,
                'latitude': data.get('latitude'),
                'longitude': data.get('longitude'),
                #'status': 'success',
            })
        except Exception as e:
            self.create({
                'name': 'Tracking Failed',
                'user_id': lead.user_id.id,
                'lead_id': lead.id,
                #'status': 'failed',
                #'error_message': str(e),
            })

    def _generate_daily_tracking_notifications(self):
        today = fields.Date.context_today(self)
        yesterday = today - timedelta(days=1)

        # All logs created in the last 24 hours
        logs = self.env['crm.lead.tracking.log'].sudo().search([
            ('timestamp', '>=', yesterday),
            ('timestamp', '<', today)
        ])

        tracked_user_ids = set(logs.mapped('user_id').ids)

        all_users = self.env['res.users'].sudo().search([
            ('external_tracking_id', '!=', False),
            ('share', '=', False),
            ('active', '=', True),
        ])

        for user in all_users:
            tracked = user.id in tracked_user_ids
            self.env['mail.message'].create({
                'subject': 'Tracking ' + ('Success' if tracked else 'Failed'),
                'body': f'User {user.name} was ' + ('successfully tracked.' if tracked else 'not tracked in the last 24 hours.'),
                'model': 'res.users',
                'res_id': user.id,
                'message_type': 'notification',
                'subtype_id': self.env.ref('mail.mt_note').id,
                'author_id': self.env.user.partner_id.id,
            })



class CrmLead(models.Model):
    _inherit = 'crm.lead'

    @api.model_create_multi
    def create(self, vals_list):
        leads = super().create(vals_list)
        for lead in leads:
            if lead.user_id:
                self.env['crm.lead.tracking.log'].create_tracking_log(lead)
        return leads