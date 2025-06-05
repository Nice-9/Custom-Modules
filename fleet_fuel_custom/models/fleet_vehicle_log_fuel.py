from odoo import models, fields, api

class FleetVehicleLogFuel(models.Model):
    _name = 'fleet.vehicle.log.fuel'
    _description = 'Fleet Vehicle Log Fuel'

    cost_per_litre = fields.Float(string='Cost per Litre')
    litres_estimated = fields.Float(string='Estimated Litres')
    distance_estimated = fields.Float(string='Estimated Distance (km)')
    consumption_rate_estimated = fields.Float(string='Estimated Consumption Rate (km/l)', compute='_compute_estimation_fields', store=True)
    total_cost_estimated = fields.Float(string='Estimated Total Cost', compute='_compute_estimation_fields', store=True)
    fuel_variance = fields.Float(string='Fuel Variance (Actual - Estimated)', compute='_compute_variance', store=True)
    consumption_variance = fields.Float(string='Consumption Variance (km/l)', compute='_compute_variance', store=True)

    trip_id = fields.Many2one('fleet.vehicle.trip', string='Trip')
    driver_id = fields.Many2one('res.partner', string='Driver', domain="[('is_driver','=',True)]")

    @api.depends('cost_per_litre', 'litres_estimated')
    def _compute_estimation_fields(self):
        for rec in self:
            rec.total_cost_estimated = rec.cost_per_litre * rec.litres_estimated if rec.cost_per_litre and rec.litres_estimated else 0.0
            rec.consumption_rate_estimated = rec.distance_estimated / rec.litres_estimated if rec.litres_estimated else 0.0

    @api.depends('liter', 'litres_estimated', 'distance_estimated')
    def _compute_variance(self):
        for rec in self:
            rec.fuel_variance = rec.liter - rec.litres_estimated if rec.litres_estimated else 0.0
            actual_consumption = rec.distance_estimated / rec.liter if rec.liter else 0.0
            rec.consumption_variance = actual_consumption - rec.consumption_rate_estimated
