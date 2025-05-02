# -*- coding: utf-8 -*-

from odoo import models, fields, api


class SaleOrder(models.Model):
    _inherit = "sale.order"

    subscription_type_id = fields.Many2one("subscription.type")
    subscription_type_code = fields.Selection([("AEP", "AEP"), ("CPP", "CPP"),("DEP","DEP"),("MEM","MEM")],related="subscription_type_id.code")


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    subscription_type_id = fields.Many2one("subscription.type")
    subscription_type_code = fields.Selection([("AEP", "AEP"), ("CPP", "CPP"),("DEP","DEP"),("MEM","MEM")],related="subscription_type_id.code")
    