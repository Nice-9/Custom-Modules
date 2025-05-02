# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models, api


class PosConfigFiscalPrinter(models.Model):
    """Add Fiscal printer fields."""

    _inherit = "pos.config"

    pos_esd_devices = fields.Boolean()
    iface_fiscal_printer_ip_address = fields.Char(
        "Fiscal Printer IP Address",
        store=True,
        size=45,
        compute="_compute_fiscal_printer_ip_address",
    )
    client_app_ip = fields.Char(string="Client App IP")
    client_app_port = fields.Char(default=6001)

    response_type = fields.Selection(
        [
            ("test", "Test"),
            ("enq", "Enquiry"),
            ("get", "Get"),
            ("silent", "Silent"),
            ("display", "Display"),
        ],
        default="enq",
        help="Response from Printer",
    )

    @api.onchange("pos_esd_devices")
    def _onchange_pos_esd_devices(self):
        for record in self:
            if not record.pos_esd_devices:
                record.client_app_port = None
                record.client_app_ip = None

    @api.depends("client_app_ip", "client_app_port")
    def _compute_fiscal_printer_ip_address(self):
        for record in self:
            if record.client_app_ip and record.client_app_port:
                record.iface_fiscal_printer_ip_address = (
                    record.client_app_ip + ":" + record.client_app_port
                )
            else:
                record.iface_fiscal_printer_ip_address = ""
