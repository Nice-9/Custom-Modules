# -*- coding: utf-8 -*-

from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    is_esd_printer_enabled = fields.Boolean(
        string="Use ESD Printer",
        related="company_id.is_esd_printer_enabled",
        readonly=False,
    )
    esd_printer_ip = fields.Char(related="company_id.esd_printer_ip", readonly=False)
    esd_printer_port = fields.Char(
        related="company_id.esd_printer_port", readonly=False
    )
    esd_printer_ip_address = fields.Char(related="company_id.esd_printer_ip_address")
    response_type = fields.Selection(related="company_id.response_type", readonly=False)
    esd_exemption_hs_code = fields.Char(
        related="company_id.esd_exemption_hs_code", readonly=False
    )
    esd_exemption_tax_id = fields.Many2one(
        related="company_id.esd_exemption_tax_id", readonly=False
    )
