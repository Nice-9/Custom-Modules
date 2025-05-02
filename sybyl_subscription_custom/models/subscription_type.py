# -*- coding: utf-8 -*-

from odoo import models, fields


class SubscriptionType(models.Model):
    _name = "subscription.type"
    _description = "Subscription Type"
    _rec_name = 'display_name'

    name = fields.Char(required=True)
    code = fields.Selection([("AEP", "AEP"), ("CPP", "CPP"),("DEP","DEP"),("MEM","MEM")], required=True,help="CODE reprsent below specification:\n"\
        "[AEP] : Annual Entry Pass \n"\
        "[CPP] : Car Parking Pass \n"\
        "[DEP] :  Dog Entry Pass\n"\
        "[MEM] : Membership\n")
    display_name = fields.Char(compute="_compute_display_name")

    def _compute_display_name(self):
        for rec in self:
            rec.display_name = '[%s] %s'%(rec.code,rec.name)
