# -*- coding: utf-8 -*-

from odoo import fields, models, api


class ResCompany(models.Model):
    _inherit = "res.company"

    is_esd_printer_enabled = fields.Boolean(string="Use ESD Printer", default=False)
    esd_printer_ip = fields.Char(string="ESD Printer IP", default="192.168.0.1")
    esd_printer_port = fields.Char(string="ESD Printer PORT", default=6001)
    esd_printer_ip_address = fields.Char(
        string="ESD Printer IP Address",
        compute="_compute_fiscal_esd_printer_ip_address",
    )
    esd_exemption_hs_code = fields.Char(default="0001.12.00")
    esd_exemption_tax_id = fields.Many2one("account.tax", "Tax", help="Tax account")

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

    @api.depends("esd_printer_ip", "esd_printer_port")
    def _compute_fiscal_esd_printer_ip_address(self):
        for record in self:
            if record.esd_printer_ip and record.esd_printer_port:
                record.esd_printer_ip_address = (
                    record.esd_printer_ip + ":" + record.esd_printer_port
                )
            else:
                record.esd_printer_ip_address = ""
