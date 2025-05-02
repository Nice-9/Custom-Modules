# -*- coding: utf-8 -*-

from odoo import models, fields, api

class DogBreed(models.Model):
    _name = "dog.breed"
    _description = "Dog Breed"

    name = fields.Char(string="Breed Name", required=True)


class SubscriptionDog(models.Model):
    _name = "subscription.dog"
    _inherit = ['mail.thread', 'mail.activity.mixin', 'utm.mixin']
    _description = "Subscription Dog"

    name = fields.Char("Dog Name", required=True, tracking=True)
    image = fields.Image(required=True)
    gender = fields.Selection([("male", "Male"), ("female", "Female")], required=True, tracking=True)
    owner_id = fields.Many2one(
        "res.partner", required=True, readonly=True, domain=[("is_company", "=", False)], tracking=True
    )
    breed_id = fields.Many2one("dog.breed", required=True, tracking=True)
    vaccination_certificate = fields.Binary(required=True)
    next_vaccination_date = fields.Date(required=True, tracking=True)
    qr_code = fields.Image(related="owner_id.qr") #remove related if you remove customer_product_qrcode module from depends
    description = fields.Text()
    vaccination_certificate_name = fields.Char()
    color = fields.Selection([
            ('Black', 'Black'),
            ('White', 'White'),
            ('Brown', 'Brown'),
            ('Tan', 'Tan'),
            ('Grey', 'Grey'),
        ], required=True)
    subscription_count = fields.Integer(related="owner_id.subscription_count",store=True)
    check_in_out_state = fields.Boolean(default=True)
    # partner_checkin_history_ids = fields.Many2many("partner.checkin.history")