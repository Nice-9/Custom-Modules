# -*- coding: utf-8 -*-
from odoo import fields, models


class SurveyQuestionAnswer(models.Model):
    _inherit = "survey.question.answer"

    subscription_type_id = fields.Many2one("subscription.type")
