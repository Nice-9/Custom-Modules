# -*- coding: utf-8 -*-

from odoo import fields, models


class SurveyProductLines(models.Model):
    _inherit = "survey.product.line"

    subscription_type_id = fields.Many2one("subscription.type")
