from odoo import models, fields, api

class FleetVehicleTrip(models.Model):
    _name = 'fleet.vehicle.trip'
    _description = 'Fleet Vehicle Trip'

    name = fields.Char(string='Trip Name', required=True)
    vehicle_id = fields.Many2one('fleet.vehicle', string='Vehicle', required=True)
    driver_id = fields.Many2one('res.partner', string='Driver', domain="[('is_driver','=',True)]")
    start_time = fields.Datetime(string='Start Time', required=True)
    end_time = fields.Datetime(string='End Time')
    origin = fields.Char(string='Origin')
    destination = fields.Char(string='Destination')
    distance_planned = fields.Float(string='Planned Distance (km)')
    distance_actual = fields.Float(string='Actual Distance (km)')
    fuel_log_ids = fields.One2many('fleet.vehicle.log.fuel', 'trip_id', string='Fuel Logs')
    duration_hours = fields.Float(string='Trip Duration (hrs)', compute='_compute_duration', store=True)

    @api.depends('start_time', 'end_time')
    def _compute_duration(self):
        for rec in self:
            if rec.start_time and rec.end_time:
                delta = rec.end_time - rec.start_time
                rec.duration_hours = delta.total_seconds() / 3600.0
            else:
                rec.duration_hours = 0.0
