# -*- coding: utf-8 -*-

from odoo import models, fields, api


class ResPartner(models.Model):
    _inherit = "res.partner"

    dog_ids = fields.One2many("subscription.dog", "owner_id")
    car_ids = fields.One2many("subscription.vehicle", "owner_id")
