# -*- coding: utf-8 -*-

from odoo import models, fields, api

class SubscriptionVehicle(models.Model):
    _name = "subscription.vehicle"
    _inherit = ['mail.thread', 'mail.activity.mixin', 'utm.mixin']
    _description = "Subscription Vehicle"

    name = fields.Char(string="Registration Number", required=True, unique=True, tracking=True)
    image = fields.Image(required=True)
    owner_id = fields.Many2one(
        "res.partner", required=True, readonly=True, domain=[("is_company", "=", False)]
    )
    qr_code = fields.Image(related="owner_id.qr") #remove related if you remove customer_product_qrcode module from depends
    description = fields.Text()
    check_in_out_state = fields.Boolean(default=True)
    color = fields.Selection([
            ('Black', 'Black'),
            ('White', 'White'),
            ('Silver', 'Silver'),
            ('Grey', 'Grey'),
            ('Red', 'Red'),
            ('Blue', 'Blue'),
            ('Green', 'Green'),
            ('Brown', 'Brown'),
            ('Yellow', 'Yellow'),
            ('Orange', 'Orange'),
            ('Custom Color', 'Custom Color'),
            ('Wrapped', 'Wrapped')
        ], required=True)
    subscription_count = fields.Integer(related="owner_id.subscription_count",store=True)
    # partner_checkin_history_ids = fields.Many2many("partner.checkin.history")
