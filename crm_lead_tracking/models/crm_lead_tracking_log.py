import requests
from odoo import models, fields, api
from odoo.exceptions import UserError
from datetime import datetime, timedelta
import logging

_logger = logging.getLogger(__name__)
# class CrmLeadTrackingLog(models.Model):
#     _name = 'crm.lead.tracking.log'
#     _description = 'CRM Lead Tracking Log'
#     _order = 'date desc'

#     name = fields.Char(string='Location Name')
#     date = fields.Datetime(string='Date', default=fields.Datetime.now)
#     user_id = fields.Many2one('res.users', string='Salesperson', default=lambda self: self.env.user)
#     lead_id = fields.Many2one('crm.lead', string='CRM Lead')
#     latitude = fields.Float(string='Latitude')
#     longitude = fields.Float(string='Longitude')

#     #status = fields.Selection([('success', 'Success'), ('failed', 'Failed')], string='Status', default='success')
#     #error_message = fields.Text(string="Error", readonly=True)

#     @api.model
#     def create_tracking_log(self, lead):
#         try:
            
#             #api_url = f"http://178.128.158.75:30002/api/location/live/{res.partnerr_id}"
#             partner_id = lead.user_id.partner_id
#             api_url = f"https://apideylin.dibon.co.ke/api/location/live/{partner_id}"
#             if not api_url:
#                 raise UserError("Tracking API URL or token not configured in system parameters.")
#             response = requests.get(api_url, timeout=20)
#             if response.status_code != 200:
#                 raise UserError(f"Tracking API error: {response.text}")
#             data = response.json()
            
#             # API Call for location name conversion
#             longitude = data.get('longitude')
#             latitude = data.get('latitude')
            
#             # cla# Define the URL
#             url = "https://apideylin.dibon.co.ke/api/location/address"
#             params = {
#                 "latitude": latitude,
#                 "longitude": longitude,
#             }

#             try:
#                 # Send GET request
#                 response = requests.get(url, params=params)
#                 response.raise_for_status()  # Raise an error for bad status codes

#                 # Parse JSON response
#                 name = response.json()
#                 name = name['full_address']
#                 print("Response:", name)

#             except requests.exceptions.RequestException as e:
#                 print("Error:", e)
#                 name = "Unknown Location"



#             self.create({
#                 'name': partner_id,
#                 'user_id': lead.user_id.id,
#                 'lead_id': lead.id,
#                 'latitude': data.get('latitude'),
#                 'longitude': data.get('longitude'),
#                 #'status': 'success',
#             })
#         except Exception as e:
#             self.create({
#                 'name': 'Offline',
#                 'user_id': lead.user_id.id,
#                 'lead_id': lead.id,
#                 #'status': 'failed',
#                 #'error_message': str(e),
#             })

#     def _generate_daily_tracking_notifications(self):
#         today = fields.Date.context_today(self)
#         yesterday = today - timedelta(days=1)

#         # All logs created in the last 24 hours
#         logs = self.env['crm.lead.tracking.log'].sudo().search([
#             ('timestamp', '>=', yesterday),
#             ('timestamp', '<', today)
#         ])

#         tracked_user_ids = set(logs.mapped('user_id').ids)

#         all_users = self.env['res.users'].sudo().search([
#             ('external_tracking_id', '!=', False),
#             ('share', '=', False),
#             ('active', '=', True),
#         ])

#         for user in all_users:
#             tracked = user.id in tracked_user_ids
#             self.env['mail.message'].create({
#                 'subject': 'Tracking ' + ('Success' if tracked else 'Failed'),
#                 'body': f'User {user.name} was ' + ('successfully tracked.' if tracked else 'not tracked in the last 24 hours.'),
#                 'model': 'res.users',
#                 'res_id': user.id,
#                 'message_type': 'notification',
#                 'subtype_id': self.env.ref('mail.mt_note').id,
#                 'author_id': self.env.user.partner_id.id,
#             })



# class CrmLead(models.Model):
#     _inherit = 'crm.lead'

#     @api.model_create_multi
#     def create(self, vals_list):
#         leads = super().create(vals_list)
#         for lead in leads:
#             if lead.user_id:
#                 self.env['crm.lead.tracking.log'].create_tracking_log(lead)
#         return leads

class CrmLeadTrackingLog(models.Model):
    _name = 'crm.lead.tracking.log'
    _description = 'CRM Lead Tracking Log'
    _order = 'date desc'

    # Fields for display on frontend
    name = fields.Char(string='Location Name', compute='_compute_location_name', store=True)
    date = fields.Datetime(string='Date', default=fields.Datetime.now)
    user_id = fields.Many2one('res.users', string='Salesperson', default=lambda self: self.env.user)
    lead_id = fields.Many2one('crm.lead', string='CRM Lead')
    latitude = fields.Float(string='Latitude', digits=(16, 6))
    longitude = fields.Float(string='Longitude', digits=(16, 6))
    full_address = fields.Text(string='Full Address')
    coordinates = fields.Char(string='Coordinates', compute='_compute_coordinates', store=True)

    # Computed fields for frontend display
    @api.depends('latitude', 'longitude')
    def _compute_coordinates(self):
        for record in self:
            if record.latitude and record.longitude:
                record.coordinates = f"Lat: {record.latitude:.6f}, Long: {record.longitude:.6f}"
            else:
                record.coordinates = "No coordinates available"

    @api.depends('full_address')
    def _compute_location_name(self):
        for record in self:
            record.name = record.full_address if record.full_address else "Location unknown"

    @api.model
    def _get_location_coordinates(self, device_address):
        """Step 1: Get coordinates from device address"""
        try:
            api_url = f"https://apideylin.dibon.co.ke/api/location/live/{device_address}"
            response = requests.get(api_url, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            if not data.get('latitude') or not data.get('longitude'):
                raise UserError(_("Invalid coordinates received from API"))
            
            return {
                'latitude': float(data['latitude']),
                'longitude': float(data['longitude'])
            }
        except requests.exceptions.RequestException as e:
            _logger.error(f"Coordinates API failed for partner {device_address}: {str(e)}")
            raise UserError(_("Could not fetch coordinates: %s") % str(e))

    @api.model
    def _get_location_name(self, latitude, longitude):
        """Step 2: Get location name from coordinates"""
        try:
            url = "https://apideylin.dibon.co.ke/api/location/address"
            response = requests.get(url, params={
                'latitude': latitude,
                'longitude': longitude
            }, timeout=10)
            response.raise_for_status()
            return response.json().get('full_address', 'Unknown Location')
        except requests.exceptions.RequestException as e:
            _logger.warning(f"Reverse geocoding failed for {latitude},{longitude}: {str(e)}")
            return f"Location at {latitude:.6f}, {longitude:.6f}"

    @api.model
    def create_tracking_log(self, lead):
        """Main method that orchestrates the sequence"""
        try:
            if not lead.user_id or not lead.user_id.device_address:
                raise UserError(_("No valid salesperson assigned to this lead"))

            device_address = lead.user_id.device_address.id
            
            # Step 1: Get coordinates using device address
            coordinates = self._get_location_coordinates(device_address)
            
            # Step 2: Get location name using coordinates
            full_address = self._get_location_name(
                coordinates['latitude'], 
                coordinates['longitude']
            )
            
            # Create and return the log record
            return self.create({
                'lead_id': lead.id,
                'user_id': lead.user_id.id,
                'latitude': coordinates['latitude'],
                'longitude': coordinates['longitude'],
                'full_address': full_address,
            })

        except Exception as e:
            _logger.error(f"Tracking failed for lead {lead.id}: {str(e)}")
            return self.create({
                'lead_id': lead.id,
                'user_id': lead.user_id.id if lead.user_id else False,
                'full_address': f"Tracking error: {str(e)}",
            })


class CrmLead(models.Model):
    _inherit = 'crm.lead'

    tracking_log_ids = fields.One2many(
        'crm.lead.tracking.log', 
        'lead_id', 
        string='Location History',
        help="Tracking history showing salesperson locations"
    )

    def action_view_location_history(self):
        """Button to view location history in frontend"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Location History'),
            'res_model': 'crm.lead.tracking.log',
            'view_mode': 'tree,form',
            'domain': [('lead_id', '=', self.id)],
            'context': {
                'default_lead_id': self.id,
                'default_user_id': self.user_id.id
            },
        }

    @api.model_create_multi
    def create(self, vals_list):
        leads = super().create(vals_list)
        for lead in leads.filtered(lambda l: l.user_id):
            self.env['crm.lead.tracking.log'].create_tracking_log(lead)
        return leads




