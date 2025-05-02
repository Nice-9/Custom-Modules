# -*- coding: utf-8 -*-
################################################################################
#
#    Kolpolok Ltd. (https://www.kolpolok.com)
#    Author: Kaushik Ahmed Apu, Zarin Tasnim, Aqil Mahmud(<https://www.kolpolok.com>)
#
################################################################################
from odoo import api, fields, models, _


class CustomUser(models.Model):
    _inherit = "res.users"

    user_ids = fields.One2many('user','user_id')

    def action_create_user(self):
        self.ensure_one()
        self.env['user'].create(dict(
            name=self.name,
            login=self.login,
        ))
