# -*- coding: utf-8 -*-

import json
import textwrap
from datetime import datetime
from odoo import api, fields, models, _


class SurveyUserInputLine(models.Model):
    _inherit = "survey.user_input.line"

    value_subscription_type_id = fields.Many2one(
        related="suggested_answer_id.subscription_type_id", store=True
    )
