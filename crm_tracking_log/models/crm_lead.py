from odoo import models
import requests
import logging

_logger = logging.getLogger(__name__)

class CrmLead(models.Model):
    _inherit = 'crm.lead'

    def create(self, vals_list):
        leads = super().create(vals_list)
        latest_lead = leads.sorted(lambda l: l.id)[-1]

        if latest_lead.user_id:
            latest_lead._log_salesperson_location()

        return leads

    def _log_salesperson_location(self):
        self.ensure_one()

        user = self.user_id
        try:
            api_url = f"http://178.128.158.75:30002/api/location/live/681de92f991d3c3f0e2f9817"
            response = requests.get(api_url, timeout=5)
            response.raise_for_status()
            data = response.json()

            self.env['crm.lead.tracking.log'].create({
                'lead_id': self.id,
                'user_id': user.id,
                #'city': data.get('city'),
                #'country': data.get('country'),
                'latitude': data.get('latitude'),
                'longitude': data.get('longitude'),
                #'status': 'success',
                #'message': 'Fetched location from tracking API.'
            })

        except requests.exceptions.RequestException as e:
            _logger.error("Failed to fetch location for user %s: %s", user.name, str(e))
            self.env['crm.lead.tracking.log'].create({
                'lead_id': self.id,
                'user_id': user.id,
                'status': 'failed',
                'message': f"Error fetching location: {str(e)}"
            })
