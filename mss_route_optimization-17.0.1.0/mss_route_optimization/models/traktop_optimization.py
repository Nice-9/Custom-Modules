import requests
from odoo import api, fields, models, _, _lt
from odoo.tools import get_timedelta
from odoo.exceptions import ValidationError
from math import radians, sin, cos, sqrt, atan2
from odoo import models, fields, api
import requests
import logging
import re
import json
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class Traktop(models.Model):
    _name = 'traktop'
    _description = 'Trakop'
    _inherit = ['mail.thread']
    active = fields.Boolean(string="Active", default=True)

    sale_order_id = fields.Many2one('sale.order', string="Sale Order")
    partner_id = fields.Many2one('res.partner', string="Customer")
    delivery_address = fields.Char(string="Delivery Address")
    partner_latitude = fields.Float('Latitude', digits=(10, 7))
    partner_longitude = fields.Float('Longitude', digits=(10, 7))
    delivery_date = fields.Datetime(string='Delivery Date')
    distance = fields.Float(string="Distance (km)")
    vehicle_id = fields.Many2one('fleet.vehicle', string="Vehicle")
    vehicle_name = fields.Char(string="Vehicle Name")
    

    
    display_name = fields.Char(
        string="Display Name", compute="_compute_display_name"
    )

    @api.depends('partner_id', 'sale_order_id')  # Ensure sale_order_id is correctly defined
    def _compute_display_name(self):
        for record in self:
            partner_name = record.partner_id.name.upper() if record.partner_id else ''
            sale_order_id = record.sale_order_id.name if record.sale_order_id else ''
            record.display_name = f"{partner_name} - {sale_order_id}" if sale_order_id else partner_name




    def get_delivery_locations(self):
        """Get all delivery locations for map display"""
        # Fetch all records ordered by route_id and sequence
        locations = self.search([])
        result = []

        # Group locations by route
        routes = {}
        for loc in locations:
            if loc.route_id not in routes:
                routes[loc.route_id] = []
            routes[loc.route_id].append({
                "name": loc.name,
                "latitude": loc.partner_latitude,
                "longitude": loc.partner_longitude,
                "sequence": loc.route_sequence,
                "type": loc.step_type,
            })

        # Sort locations within each route
        for route_id in routes:
            routes[route_id].sort(key=lambda x: x["sequence"])

        return {
            "routes": routes
        }

    @api.model
    def fetch_vehicle_data(self):
        """Fetch vehicle data from the 'fleet.vehicle' model."""
        vehicles = self.env['fleet.vehicle'].search([])  # Fetch all vehicles
        vehicle_data = []
        for vehicle in vehicles:
            if vehicle.location:
                location_str = vehicle.location.strip()
                location_data = re.findall(r"[-+]?\d*\.\d+|\d+", location_str)
                if len(location_data) == 2:
                    try:
                        latitude = float(location_data[1])  # Latitude
                        longitude = float(location_data[0])  # Longitude
                        start_point = [latitude, longitude]
                        end_point = [latitude, longitude]
                        vehicle_data.append({
                            "id": vehicle.id,
                            "vehicle_name": 'car',
                            "start": start_point,
                            "end": end_point
                        })
                    except ValueError:
                        _logger.error(f"Invalid location format for vehicle {vehicle.name}: {vehicle.location}")
        return vehicle_data

    @api.model
    def fetch_jobs_data(self):
        """Fetch jobs data from the 'sale.order' model."""
        confirmed_orders = self.env['sale.order'].search([('state', '=', 'sale')])
        job_data = []
        for order in confirmed_orders:
            if order.partner_id.partner_latitude and order.partner_id.partner_longitude:
                location = [order.partner_id.partner_longitude, order.partner_id.partner_latitude]
                job_data.append({
                    "id": order.id,
                    "oid": order.name,
                    "user_id": str(order.partner_id.id),
                    "location": location,
                    'delivery_date': order.commitment_date.isoformat() if order.commitment_date else None,
                    'partner_latitude': order.partner_shipping_id.partner_latitude,
                    'partner_longitude': order.partner_shipping_id.partner_longitude,

                })
        return job_data

    @api.model
    def integrate_vroom(self):
        """Integrate with the Routing API to optimize routes."""
        vroom_url = "https://route.trakop.com:8100"
        vehicles = self.fetch_vehicle_data()
        jobs = self.fetch_jobs_data()

        # Convert datetime fields to string for JSON serialization
        for job in jobs:
            if job.get('delivery_date'):
                job['delivery_date'] = job['delivery_date'].isoformat()

        payload = {
            "vehicles": vehicles,
            "jobs": jobs
        }

        try:
            _logger.info(
                f"Sending payload to Routing API: {json.dumps(payload, indent=4)}")  # Log payload as formatted JSON

            # Send POST request to Routing API
            response = requests.post(vroom_url, json=payload, timeout=30)
            print('response', response)
            response.raise_for_status()
            optimized_routes = response.json()
            return optimized_routes

        except requests.exceptions.RequestException as e:
            _logger.error(f"Error while connecting to Routing API: Either partners or vehicles Latitude and Longitude are missing.")
            _logger.error(
                f"Payload sent to Routing API: {json.dumps(payload, indent=4)}")  # Log payload as formatted JSON
            if 'response' in locals():
                _logger.error(f"Response content: {response.text}")
            raise UserError(f"Error connecting to Routing API: Either partners or vehicles Latitude and Longitude are missing.")

    @api.model
    def action_fetch_sale_orders(self):
        # Your existing logic here
        confirmed_sale_orders = self.env['sale.order'].search([('state', '=', 'sale')])
        existing_sale_order_ids = self.search([]).mapped('sale_order_id.id')

        # Create new records for sale orders not already linked
        for order in confirmed_sale_orders:
            if order.id not in existing_sale_order_ids:
                self.create({
                    'sale_order_id': order.id,
                    'partner_id': order.partner_shipping_id.id,
                    'delivery_address': order.partner_shipping_id.contact_address,
                    'delivery_date': order.commitment_date,
                    'partner_latitude': order.partner_shipping_id.partner_latitude,
                    'partner_longitude': order.partner_shipping_id.partner_longitude,
                })
        
    def disable_cron_after_install(self):
        cron = self.env.ref('traktop.ir_cron_action_fetch_sale_orders', False)
        if cron:
            cron.write({'active': False})  # Disable the cron after first run


    # def get_optimized_rec_created(self):
    #     try:
    #         # Get optimized routes from Routing
    #         optimized_data = self.integrate_vroom()
    #         # Delete existing records
    #         existing_records = self.search([])
    #         existing_records.unlink()

    #         # Process each route
    #         for route in optimized_data.get('routes', []):
    #             vehicle_id = route.get('vehicle')
    #             vehicle_rec = self.env['fleet.vehicle'].search([("id", "=", vehicle_id)])
    #             vechile = vehicle_rec.driver_id.id

    #             # Process each step in the route
    #             for step_idx, step in enumerate(route.get('steps', [])):
    #                 step_type = step.get('type')

    #                 # Prepare the vals dictionary
    #                 vals = {

    #                 }

    #                 if step_type == 'start':
    #                     vals.update({
    #                         'partner_id': vechile,
    #                     })
    #                 elif step_type == 'end':
    #                     vals.update({
    #                         'partner_id': vechile,
    #                     })
    #                 elif step_type == 'job':
    #                     job_id = step.get('job')
    #                     sale_order = self.env['sale.order'].browse(job_id)
    #                     if sale_order:
    #                         vals.update({
    #                             'sale_order_id': sale_order.id,
    #                             'partner_id': sale_order.partner_shipping_id.id,
    #                             'delivery_address': sale_order.partner_shipping_id.contact_address,
    #                             'delivery_date': sale_order.commitment_date,
    #                             'partner_latitude': sale_order.partner_shipping_id.partner_latitude,
    #                             'partner_longitude': sale_order.partner_shipping_id.partner_longitude,
    #                         })

    #                 self.create(vals)

    #         return {
    #             'type': 'ir.actions.client',
    #             'tag': 'display_notification',
    #             'params': {
    #                 'title': _('Success'),
    #                 'message': _('Optimized routes have been computed and records created successfully.'),
    #                 'sticky': False,
    #                 'type': 'success',
    #             }
    #         }
    #     except Exception as e:
    #         raise UserError(_('Error computing optimized routes: %s') % str(e))



    # def get_optimized_rec_created(self):
    #     try:
    #         # Get optimized routes from Routing
    #         optimized_data = self.integrate_vroom()

    #         # Delete existing records
    #         existing_records = self.search([])
    #         existing_records.unlink()

    #         # Process each route
    #         for route in optimized_data.get('routes', []):
    #             vehicle_id = route.get('vehicle')
    #             vehicle_rec = self.env['fleet.vehicle'].search([("id", "=", vehicle_id)])

    #             if not vehicle_rec:
    #                 _logger.warning(f"Vehicle with ID {vehicle_id} not found.")
    #                 continue

    #             # Assign vehicle driver or appropriate partner
    #             partner_id = vehicle_rec.driver_id.partner_id.id if vehicle_rec.driver_id else False

    #             # Process each step in the route
    #             for step_idx, step in enumerate(route.get('steps', [])):
    #                 step_type = step.get('type')

    #                 # Prepare the vals dictionary
    #                 vals = {
    #                     'vehicle_id': vehicle_rec.id,  # Link vehicle to the record
    #                     'vehicle_name': vehicle_rec.name,  # Optional: Assign vehicle name
    #                 }

    #                 if step_type == 'start':
    #                     # Assuming start step is related to vehicle's driver or assigned partner
    #                     vals.update({
    #                         'partner_id': partner_id,
    #                     })
    #                 elif step_type == 'end':
    #                     # Assuming end step is related to vehicle's driver or assigned partner
    #                     vals.update({
    #                         'partner_id': partner_id,
    #                     })
    #                 elif step_type == 'job':
    #                     job_id = step.get('job')
    #                     sale_order = self.env['sale.order'].browse(job_id)

    #                     if sale_order:
    #                         vals.update({
    #                             'sale_order_id': sale_order.id,
    #                             'partner_id': sale_order.partner_shipping_id.id,
    #                             'delivery_address': sale_order.partner_shipping_id.contact_address,
    #                             'delivery_date': sale_order.commitment_date,
    #                             'partner_latitude': sale_order.partner_shipping_id.partner_latitude,
    #                             'partner_longitude': sale_order.partner_shipping_id.partner_longitude,
    #                         })

    #                 # Create record with the processed values
    #                 self.create(vals)

    #         # Return success notification
    #         return {
    #             'type': 'ir.actions.client',
    #             'tag': 'display_notification',
    #             'params': {
    #                 'title': _('Success'),
    #                 'message': _('Optimized routes have been computed and records created successfully.'),
    #                 'sticky': False,
    #                 'type': 'success',
    #             }
    #         }

    #     except Exception as e:
    #         # Handle exception and show error message
    #         raise UserError(_('Error computing optimized routes: %s') % str(e))

    def get_optimized_rec_created(self):
        try:
            # Get optimized routes from Routing
            optimized_data = self.integrate_vroom()

            # Delete existing records
            existing_records = self.search([])
            existing_records.unlink()

            # Process each route
            for route in optimized_data.get('routes', []):
                vehicle_id = route.get('vehicle')
                vehicle_rec = self.env['fleet.vehicle'].search([("id", "=", vehicle_id)])

                if not vehicle_rec:
                    _logger.warning(f"Vehicle with ID {vehicle_id} not found.")
                    continue

                # Assign vehicle driver or appropriate partner
                partner_id = vehicle_rec.driver_id.id if vehicle_rec.driver_id else False

                # Process each step in the route
                for step_idx, step in enumerate(route.get('steps', [])):
                    step_type = step.get('type')

                    # Prepare the vals dictionary
                    vals = {
                        'vehicle_id': vehicle_rec.id,  # Link vehicle to the record
                        'vehicle_name': vehicle_rec.name,  # Optional: Assign vehicle name
                    }

                    if step_type == 'start':
                        vals.update({
                            'partner_id': partner_id,
                        })
                    elif step_type == 'end':
                        vals.update({
                            'partner_id': partner_id,
                        })
                    elif step_type == 'job':
                        job_id = step.get('job')
                        sale_order = self.env['sale.order'].browse(job_id)

                        if sale_order:
                            vals.update({
                                'sale_order_id': sale_order.id,
                                'partner_id': sale_order.partner_shipping_id.id,
                                'delivery_address': sale_order.partner_shipping_id.contact_address,
                                'delivery_date': sale_order.commitment_date,
                                'partner_latitude': sale_order.partner_shipping_id.partner_latitude,
                                'partner_longitude': sale_order.partner_shipping_id.partner_longitude,
                            })

                    # Create record with the processed values
                    self.create(vals)

            # Return success notification
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Success'),
                    'message': _('Optimized routes have been successfully created/updated.'),
                    'type': 'success',
                    'sticky': False,
                    'next': {
                        'type': 'ir.actions.client',
                        'tag': 'reload',
                    }
                }
            }

        except Exception as e:
            # Handle exception and show error message
            raise UserError(_('Error computing optimized routes: Either partners or vehicles Latitude and Longitude are missing.'))

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    def action_confirm(self):
        res = super(SaleOrder, self).action_confirm()
        for order in self:
            tracktop_vals = {
                'sale_order_id': order.id,
                'partner_id': order.partner_shipping_id.id,
                'partner_latitude': order.partner_shipping_id.partner_latitude,
                'partner_longitude': order.partner_shipping_id.partner_longitude,
                'delivery_address': order.partner_shipping_id.contact_address,
                'delivery_date': order.commitment_date,
            }
            self.env['traktop'].create(tracktop_vals)

        return res

    def write(self, vals):
        res = super(SaleOrder, self).write(vals)

        # If the state is changing to 'cancel', update traktop
        if 'state' in vals and vals['state'] == 'cancel':
            for order in self:
                traktop_record = self.env['traktop'].search([('sale_order_id', '=', order.id)], limit=1)
                if traktop_record:
                    traktop_record.write({'active': False})  # Deactivate instead of deleting

        # If the commitment date is updated, update it in traktop
        if 'commitment_date' in vals:
            for order in self:
                traktop_record = self.env['traktop'].search([('sale_order_id', '=', order.id)], limit=1)
                if traktop_record:
                    traktop_record.write({'delivery_date': vals['commitment_date']})

        return res


    def unlink(self):
        # Delete associated traktop records before deleting the sale order
        for order in self:
            traktop_record = self.env['traktop'].search([('sale_order_id', '=', order.id)], limit=1)
            if traktop_record:
                traktop_record.unlink()

        return super(SaleOrder, self).unlink()
        
class ResPartner(models.Model):
    _inherit = 'res.partner'

    @api.model
    def create(self, vals):
        partner = super(ResPartner, self).create(vals)
        if any(field in vals for field in ['street', 'city', 'zip', 'state_id', 'country_id']):
            partner.geo_localize()
        return partner

    def write(self, vals):
        res = super(ResPartner, self).write(vals)
        if any(field in vals for field in ['street', 'city', 'zip', 'state_id', 'country_id']):
            self.geo_localize()
        return res

    def geo_localize(self):
        """Trigger the geolocation compute method"""
        for partner in self:
            if partner.street or partner.city or partner.zip or partner.state_id or partner.country_id:
                super(ResPartner, partner).geo_localize()
