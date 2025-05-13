import logging
import requests
from odoo import http
from odoo.http import request

_logger = logging.getLogger(__name__)

class TrackingController(http.Controller):

    @http.route('/tracking/live_location', type='json', auth='user', csrf=False)
    def fetch_live_location(self, id, **kwargs):
        try:
            lead = request.env['crm.lead'].browse(int(id))
            if not lead.exists():
                return {'error': 'CRM Lead not found'}

            salesperson = lead.user_id

            # Create the field on re.users model
            external_tracking_id = salesperson.x_external_tracking_id 
            if not external_tracking_id:
                return {'error': 'Salesperson external ID missing'}

            # token = request.env['ir.config_parameter'].sudo().get_param('deylin_api_access_token')
            # if not token:
            #     return {'error': 'Access token not configured'}
            
            url = f"http://178.128.158.75:30002/api/location/live/681de92f991d3c3f0e2f9817"
            
            res = requests.get(url)

            if res.status_code != 200:
                return {'error': f"API error: {res.status_code}", 'details': res.text}

            
            data = res.json()
            request.env['crm.tracking.log'].sudo().create({
                'lead_id': salesperson,
                'latitude': data.get('latitude'),
                'longitude': data.get('longitude'),
                'timestamp': data.get('timestamp'),
                'salesperson_id': data.get('salesperson_id'),
            })


            return {
                'salesperson': salesperson.name,
                'lead': lead.name,
                'location': {
                    'latitude': data.get('latitude'),
                    'longitude': data.get('longitude'),
                    'timestamp': data.get('timestamp')
                }
            }
        except Exception as e:
            _logger.exception("Live tracking fetch failed")
            return {'error': str(e)}
