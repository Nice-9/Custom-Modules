# -*- coding: utf-8 -*-

import logging
import xml
import xml.etree.ElementTree as ET

from odoo import models, fields, api
from . import fiscal_printer

_logger = logging.getLogger(__name__)


class AccountFiscalLog(models.Model):
    _name = "account.fiscal.log"
    _description = "Account Fiscal Log"
    _order = "id desc"
    _rec_name = "account_move_id"

    name = fields.Text("XML Data", required=True, readonly=True)
    # pretty_xml = fields.Text(compute="_compute_pretty_xml")
    url = fields.Text(readonly=True)
    response = fields.Text(readonly=True)
    order_response = fields.Text(readonly=True)
    url_response = fields.Text(readonly=True)
    kra_url = fields.Text(readonly=True)
    error_response = fields.Text(readonly=True)
    cashier = fields.Char(readonly=True)
    user_id = fields.Many2one("res.users", readonly=True)
    account_move_id = fields.Many2one("account.move", readonly=True)
    company_id = fields.Many2one(
        "res.company", related="account_move_id.company_id", store=True
    )
    fiscal_receipt_no = fields.Char()
    cus_no = fields.Char("CUSN")
    cui_no = fields.Char("CUIN")

    @api.depends("name")
    def _compute_pretty_xml(self):
        for record in self:
            temp = xml.dom.minidom.parseString(record.name)
            record.pretty_xml = temp.toprettyxml()

    def send_close_receipt(self):
        packets = self.generate_close_receipt()
        esd_printer_ip_address = self.company_id.esd_printer_ip_address
        fiscal_printer.print_xml_file(
            printer_ip_address=esd_printer_ip_address,
            packets=packets,
            record_id=self.account_move_id,
            user_id=self.user_id,
            print_type="account",
        )

    def generate_close_receipt(self):
        packet = ET.Element("packet")
        ET.SubElement(
            packet,
            "receipt",
            {
                "action": "close",
                "system_number": "123456",
                "cashier": str(self.cashier),
                "total": fiscal_printer.format_float(self.account_move_id.amount_total),
            },
        )
        return ET.tostring(packet)

    def get_receipt_no(self):
        # todo need to fetch using relevant receipt no. like POS Order
        esd_printer_ip_address = self.company_id.esd_printer_ip_address
        _logger.info(
            "Get receipt no. via fiscal log : IP:PORT %s" % esd_printer_ip_address
        )
        fiscal_printer.send_printer_request(
            printer_ip_address=esd_printer_ip_address,
            record_id=self.account_move_id,
            response_type="fetch_receipt",
            log_id=self.sudo(),
        )

    def send_printer_request_action(self):
        esd_printer_ip_address = self.company_id.esd_printer_ip_address
        response_type = self.company_id.response_type
        _logger.info(
            "Check Printer State via fiscal log : IP:PORT %s" % esd_printer_ip_address
        )
        fiscal_printer.send_printer_request(
            printer_ip_address=esd_printer_ip_address,
            record_id=self.account_move_id,
            response_type=response_type,
            log_id=self.sudo(),
        )
