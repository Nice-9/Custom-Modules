# -*- coding: utf-8 -*-
import logging
import xml
import xml.etree.ElementTree as ET

from odoo import models, fields, api
from . import fiscal_printer

_logger = logging.getLogger(__name__)


class FiscalLog(models.Model):
    _name = "fiscal.log"
    _description = "Fiscal Log"
    _order = "id desc"
    _rec_name = "pos_order_id"

    name = fields.Text("XML Data", required=True, readonly=True)
    # pretty_xml = fields.Text(compute="_compute_pretty_xml")
    url = fields.Text("Printer URL", readonly=True)
    response = fields.Text(readonly=True)
    order_response = fields.Text(readonly=True)
    url_response = fields.Text(readonly=True)
    error_response = fields.Text(readonly=True)
    cashier = fields.Char(readonly=True)
    user_id = fields.Many2one("res.users", readonly=True)
    pos_order_id = fields.Many2one("pos.order", readonly=True)
    fiscal_receipt_no = fields.Char(
        related="pos_order_id.fiscal_receipt_no", store=True
    )
    session_id = fields.Many2one(related="pos_order_id.session_id")
    config_id = fields.Many2one(related="session_id.config_id")
    kra_url = fields.Text(readonly=True)
    cus_no = fields.Char("CUSN")
    cui_no = fields.Char("CUIN")

    @api.depends("name")
    def _compute_pretty_xml(self):
        for record in self:
            temp = xml.dom.minidom.parseString(record.name)
            record.pretty_xml = temp.toprettyxml()

    def _compute_res_name(self):
        for record in self:
            if record.res_model and record.res_id:
                record = self.env[record.res_model].browse(record.res_id)
                record.res_name = record.display_name
            else:
                record.res_name = False

    res_name = fields.Char("Resource Name", compute="_compute_res_name")
    res_model = fields.Char(
        "Resource Model",
        readonly=True,
        help="The database object this log was related to.",
    )
    res_id = fields.Many2oneReference(
        "Resource ID",
        model_field="res_model",
        readonly=True,
        help="The record id this is referred to.",
    )

    def send_close_receipt(self):
        packets = self.generate_close_receipt()
        fiscal_printer.print_xml_file(
            printer_ip_address=self.config_id.iface_fiscal_printer_ip_address,
            packets=packets,
            record_id=self.pos_order_id,
            session_id=self.session_id,
            user_id=self.user_id,
            print_type="pos",
        )

    def generate_close_receipt(self):
        packet = ET.Element("packet")
        ET.SubElement(
            packet,
            "receipt",
            {
                "action": "close",
                "system_number": str(self.config_id.id),
                "cashier": str(self.cashier),
                "total": fiscal_printer.format_float(self.pos_order_id.amount_total),
            },
        )
        packt = ET.tostring(packet)
        return packt

    def get_receipt_no(self):
        _logger.info(
            "\nGet receipt no. for POS Order '%s' via fiscal log : IP:PORT %s"
            % (
                self.pos_order_id.name,
                self.config_id.iface_fiscal_printer_ip_address,
            )
        )
        fiscal_printer.send_printer_request(
            printer_ip_address=self.config_id.iface_fiscal_printer_ip_address,
            record_id=self.pos_order_id,
            response_type="fetch_receipt",
            log_id=self.sudo(),
        )

    def send_printer_request_action(self):
        _logger.info(
            "Check Printer State via fiscal log : IP:PORT %s"
            % self.config_id.iface_fiscal_printer_ip_address
        )
        fiscal_printer.send_printer_request(
            printer_ip_address=self.config_id.iface_fiscal_printer_ip_address,
            record_id=self.pos_order_id,
            response_type=self.config_id.response_type,
            log_id=self.sudo(),
        )
