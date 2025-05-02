# -*- coding: utf-8 -*-

import logging

import odoo.addons.sybyl_esd_pos_account_novitus.models.fiscal_printer as fiscal_printer

from odoo import http, _

_logger = logging.getLogger(__name__)


class PosController(http.Controller):
    """Routes for printing using IP printer."""

    @http.route("/hw_fiscal_printer/open_cashbox", type="json", auth="none", cors="*")
    def open_cashbox(self, **params):
        _logger.info("Fiscal Printer: OPEN CASHBOX......")
        host = params.get("ip") or "127.0.0.1"
        port = params.get("port") or 6001
        _logger.info("IP: %s, Port: %s" % (host, port))
        return {"result": True, "message": "cashbox opened"}

    @http.route("/hw_fiscal_printer/print_receipt", type="json", auth="none", cors="*")
    def print_receipt(self, **params):
        _logger.info("Fiscal Printer: PRINT RECEIPT USING FISCAL PRINTER......")
        msg = _("Could not print using the configured printer.")
        host = params.get("ip") or "127.0.0.1"
        port = params.get("port") or 6001
        packets = params.get("packets")
        _logger.info("IP: %s, Port: %s" % (host, port))
        if not packets:
            packets = """<packet><control action="beep"></control></packet>"""
        try:
            fiscal_printer.print_xml_file(
                printer_ip_address=str(host) + ":" + str(port),
                packets=packets,
                print_type="pos",
            )
        except Exception as e:
            msg += "IP: %s, Port: %s. %s" % (host, port, e)
            _logger.warning("Fiscal Printer : %s", msg)
            return {"result": False, "message": [e] or [""]}
        status = {"status": "connected"}
        return self._handle_printer_status(status)

    def _handle_printer_status(self, status):
        """Return correct format for status for javascript print module."""
        if status.get("status") == "connected":
            return {"result": True, "message": "Connected and ready to print"}
        if status.get("status") in ("error", "disconnected"):
            return {"result": False, "message": status.get("messages", [])}
