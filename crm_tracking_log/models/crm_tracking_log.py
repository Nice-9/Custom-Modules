from odoo import models, fields, api

class CRMTrackingLog(models.Model):
    _name = 'crm.tracking.log'
    _description = 'CRM Lead Tracking Log'
    _order = 'timestamp desc'

    lead_id = fields.Many2one('crm.lead', string='Lead', required=True, ondelete='cascade')
    user_id = fields.Many2one('res.users', string='Salesperson', related='lead_id.user_id', store=True)
    latitude = fields.Float('Latitude')
    longitude = fields.Float('Longitude')
    timestamp = fields.Datetime('Timestamp', default=fields.Datetime.now)

    @api.model
    def get_top_locations(self):
        self.env.cr.execute("""
            SELECT latitude, longitude, COUNT(*) as total
            FROM crm_tracking_log
            WHERE latitude IS NOT NULL AND longitude IS NOT NULL
            GROUP BY latitude, longitude
            ORDER BY total DESC
            LIMIT 5
        """)
        return self.env.cr.dictfetchall()



