# -*- coding: utf-8 -*-
import logging
import re

import xmltodict
from odoo.exceptions import ValidationError
from odoo.http import request

from odoo import _
from . import socket_client

_logger = logging.getLogger(__name__)


def format_float(value):
    return "{:.2f}".format(abs(value))


def sanitize_and_trim(my_str="", max_length=40):
    """Remove special characters from a string and trim to max_length."""
    sanitized_str = re.sub("[^a-zA-Z0-9 \\n\\.]", "", my_str)
    return sanitized_str[:max_length] if sanitized_str else ""


def clean_string(input_string, limit):
    # Use regular expressions to replace non-alphanumeric characters with an empty string
    cleaned_string = re.sub(r"[^a-zA-Z0-9]", "", input_string)
    # Trim the resulting string to the specified limit from the last
    if limit:
        cleaned_string = cleaned_string[-limit:]
    return cleaned_string
    # Trim the resulting string to the specified limit from the end
    return cleaned_string[-limit:] if limit else cleaned_string


def trim_product_name(product_name, max_length=40):
    # Trim and append ".." if necessary
    return (
        f"{product_name[:max_length - 2]}.."
        if len(product_name) > max_length
        else product_name
    )


def print_xml_file(
    printer_ip_address,
    packets=None,
    record_id=None,
    session_id=None,
    cashier=None,
    user_id=None,
    response_type=None,
    print_type=None,
):
    _logger.info("Fiscal Printer: PRINT RECEIPT USING ESD PRINTER......")
    msg = _("Could not print using the configured printer.")
    if not printer_ip_address:
        raise ValidationError(
            _("Please add IP and port in printer under configuration.")
        )

    ip_address_split = printer_ip_address.split(":")
    host = ip_address_split[0]
    port = ip_address_split[1]
    _logger.info("IP: %s, Port: %s" % (host, port))

    if not packets:
        packets = """<packet><control action="beep"></control></packet>"""
        if isinstance(packets, str):
            packets = packets.encode()
    _logger.info(
        "\nPackets DataType : %s\nPackets Value : %s" % (type(packets), packets)
    )
    values = {
        "name": packets,
        "url": printer_ip_address,
        "cashier": user_id.name if user_id else cashier,
        "user_id": user_id.id if user_id else None,
    }
    if session_id:
        values.update({"session_id": session_id.id})
    if print_type == "account":
        if record_id:
            values.update({"account_move_id": record_id.id})
        log_id = request.env["account.fiscal.log"].sudo().create(values)
    elif print_type == "pos":
        if record_id:
            values.update({"pos_order_id": record_id.id})
        log_id = request.env["fiscal.log"].sudo().create(values)
    else:
        raise ValidationError(_("Print type is missing"))
    try:
        if not printer_ip_address:
            record_id.total_attempts += 1
            return {"result": False, "status": "disconnected"}
        # Sending the Order detail to KRA Printer
        response = socket_client.socket_client_request(printer_ip_address, packets)
        log_id.order_response = response
        record_id.is_fiscal_print_done = True
        if response_type and response_type != "test" and record_id.amount_total > 0:
            counter = 0
            _logger.info("Fetching Receipt No...")
            while True:
                if response_type != "fetch_receipt":
                    response_type = False
                    packets = False
                send_printer_request(
                    printer_ip_address=printer_ip_address,
                    record_id=record_id,
                    packet=packets,
                    response_type=response_type,
                    log_id=log_id,
                )
                counter += 1
                if record_id.fiscal_receipt_no or counter > 2:
                    break
                _logger.info("Retry fetching Receipt No...")
            if not record_id.fiscal_receipt_no:
                record_id.total_attempts += 1
            else:
                _logger.info("Receipt No. : %s:" % record_id.fiscal_receipt_no)
        status = {"status": "connected"}
    except Exception as e:
        msg += "IP: %s, Port: %s. %s" % (host, port, e)
        log_id.error_response = e
        _logger.warning("Fiscal Printer : %s", msg)
        record_id.total_attempts += 1
        status = {"status": "unavailable", "result": False, "message": [e] or [""]}
    _logger.info(status)
    return status


def send_printer_request(
    printer_ip_address, record_id, response_type=None, log_id=None, packet=None
):
    if not printer_ip_address:
        raise ValidationError(
            _("Please add IP and port in printer under configuration.")
        )
    ip_address_split = printer_ip_address.split(":")
    host = ip_address_split[0]
    port = ip_address_split[1]
    _logger.info("Get Status of Latest Operation from Printer")
    if response_type == "enq":
        # it will return status of the latest operation
        enq_packet = packet
    elif response_type == "get":
        # if status show error you can read error by sequence :
        enq_packet = """<packet><error action="get" value=""></error></packet>"""
    elif response_type == "silent":
        # All errors will be returned to PC
        enq_packet = """<packet><error action="set" value="silent"></error></packet>"""
    elif response_type == "display":
        # Will return to display information
        enq_packet = """<packet><error action="set" value="display"></error></packet>"""
    elif response_type == "duplicate":
        # Will reprint the receipt in printer without sending information to KRA
        # """<packet><report type="protectedmemory" from="1" to="2" kind="receipt"></report></packet>"""
        enq_packet = packet
    elif response_type == "fetch_receipt":
        # Will fetch the receipt information like invoice number and QR.
        if record_id._name == "pos.order":
            reference = clean_string(record_id.pos_reference, 12)
        else:
            reference = clean_string(record_id.name, 12)
        enq_packet = packet = (
            """<packet><info action="receipt" trader_sys_number_EX="%s"></info></packet>"""
            % reference
        )
    else:
        enq_packet = """<packet><info action="checkout" type="receipt" lasterror="?" isfiscal="?" receiptopen="?" lastreceipterror="?" resetcount="?" date="?" receiptcount="?" cash="?" uniqueno="?" lastreceipt="?" lastinvoice="?" lastprintout="?"></info></packet>"""
    if isinstance(enq_packet, str):
        enq_packet = enq_packet.encode()
    _logger.info("Packet %s", enq_packet)
    response = socket_client.socket_client_request(printer_ip_address, enq_packet)
    if isinstance(response, bytes):
        response = response.decode()
    if log_id:
        log_id.url = printer_ip_address
    # To get KRA Registration information.
    url_response = socket_client.socket_client_request(printer_ip_address, packet)
    if isinstance(url_response, bytes):
        url_response = url_response.decode()
    _logger.info("record_id %s", record_id)
    _logger.info("response %s", response)
    _logger.info("url_response %s", url_response)
    try:
        _logger.info("recv from server: %s" % response)
        if not response:
            status = {"status": "unavailable", "result": False}
            return status
        if log_id:
            log_id.response = response
            log_id.url_response = url_response
            log_id.error_response = None
            if record_id and response:
                _logger.info("Printer Response received:")
                # Fetch Receipt No.
                try:
                    mystrip = lambda s, ss: s[: s.index(ss) + len(ss)]
                    strip = mystrip(response, "</packet>")
                    o = xmltodict.parse(strip)
                    _logger.info(o)
                    if o.get("packet") and o.get("packet").get("info"):
                        lastreceipt = o.get("packet").get("info").get("@lastreceipt")
                        receipt_number = (
                            o.get("packet").get("info").get("@receipt_number")
                        )
                        isfiscal = o.get("packet").get("info").get("@isfiscal")
                        cusn = o.get("packet").get("info").get("@CU_number")
                        cuin = (
                            o.get("packet")
                            .get("info")
                            .get("@middleware_invoice_number")
                        )
                        if isfiscal == "yes":
                            record_id.is_fiscal = True
                        else:
                            record_id.is_fiscal = False
                        value_to_assign = lastreceipt if lastreceipt else receipt_number
                        record_id.fiscal_receipt_no = value_to_assign
                        log_id.fiscal_receipt_no = value_to_assign
                        _logger.info("cusn:%s, cuin:%s", cusn, cuin)
                        record_id.cus_no = cusn
                        record_id.cui_no = cuin
                        log_id.cus_no = cusn
                        log_id.cui_no = cuin
                except Exception as e:
                    _logger.info("Exception xmltodict failed reason : %s", e)
                    result = re.search("""lastreceipt="(.*)" lastinvoice""", response)
                    is_fiscal = re.search("""isfiscal="(.*)" receiptopen""", response)
                    cuin_result = re.search(
                        'middleware_invoice_number="(.*)" qr_code_link', response
                    )
                    cusn_result = re.search('CU_number="(.*)" ', response)
                    if cusn_result:
                        cusn_value = cusn_result.group(1)
                        record_id.cus_no = cusn_value
                        log_id.cus_no = cusn_value
                        _logger.info("cusn:%s", cusn_value)
                    if cuin_result:
                        cuin_value = cuin_result_value = cuin_result.group(1)
                        if not isinstance(cuin_result_value, int):
                            int_value2 = [
                                int(s) for s in cuin_result_value.split() if s.isdigit()
                            ]
                            cuin_value = int_value2[0]
                        record_id.cui_no = cuin_value
                        log_id.cui_no = cuin_value
                        _logger.info("cuin:%s", cuin_value)
                    if result:
                        receipt_value = result_value = result.group(1)
                        if not isinstance(result_value, int):
                            int_value = [
                                int(s) for s in result_value.split() if s.isdigit()
                            ]
                            receipt_value = int_value[0]
                        record_id.fiscal_receipt_no = receipt_value
                        log_id.fiscal_receipt_no = receipt_value
                    if is_fiscal:
                        is_fiscal_value = is_fiscal.group(1)
                        if is_fiscal_value == "yes":
                            record_id.is_fiscal = True
                        else:
                            record_id.is_fiscal = False
            if record_id and url_response:
                _logger.info("Printer URL Response received:")
                start_url = end_url = False
                try:
                    mystrip = lambda s, ss: s[: s.index(ss) + len(ss)]
                    strip = mystrip(url_response, "</packet>")
                    o = xmltodict.parse(strip)
                    _logger.info(o)
                    if o.get("packet") and o.get("packet").get("info"):
                        pre_result = o.get("packet").get("info").get("@qr_code_link")
                        suffix_result = (
                            o.get("packet")
                            .get("info")
                            .get("@middleware_invoice_number")
                        )
                        cusn = o.get("packet").get("info").get("@CU_number")
                        cuin = (
                            o.get("packet")
                            .get("info")
                            .get("@middleware_invoice_number")
                        )
                        _logger.info("cusn:%s, cuin:%s", cusn, cuin)
                        if pre_result:
                            start_url = pre_result.group(1)
                        if suffix_result:
                            end_url = suffix_result.group(1)
                        if start_url and end_url:
                            full_url = start_url + end_url
                            full_url = full_url.replace("&amp;", "&")
                            log_id.kra_url = full_url
                        record_id.cus_no = cusn
                        record_id.cui_no = cuin
                        log_id.cus_no = cusn
                        log_id.cui_no = cuin
                except Exception as e:
                    _logger.info("Exception xmltodict failed reason : %s", e)
                    pre_result = re.search(
                        """qr_code_link="(.*)" CU_number""", url_response
                    )
                    suffix_result = re.search(
                        """middleware_invoice_number="(.*)" qr_code_link=""",
                        url_response,
                    )
                    cuin_result = re.search(
                        """middleware_invoice_number="(.*)" qr_code_link""",
                        url_response,
                    )
                    cusn_result = re.search("""CU_number="(.*)" """, url_response)
                    if cuin_result:
                        cuin_value = cuin_result_value = cuin_result.group(1)
                        if not isinstance(cuin_result_value, int):
                            int_value2 = [
                                int(s) for s in cuin_result_value.split() if s.isdigit()
                            ]
                            cuin_value = int_value2[0]
                        _logger.info("cuin:%s", cuin_value)
                        log_id.cui_no = cuin_value
                        record_id.cui_no = cuin_value
                    if cusn_result:
                        cusn_value = cusn_result.group(1)
                        _logger.info("cusn:%s", cusn_value)
                        log_id.cus_no = cusn_value
                        record_id.cus_no = cusn_value
                    if pre_result:
                        start_url = pre_result.group(1)
                    if suffix_result:
                        end_url = suffix_result.group(1)
                    if start_url and end_url:
                        full_url = start_url + end_url
                        full_url = full_url.replace("&amp;", "&")
                        log_id.kra_url = full_url
        status = {"status": "connected"}
    except Exception as e:
        msg = "IP: %s, Port: %s. %s" % (host, port, e)
        if log_id:
            log_id.error_response = e
        _logger.warning("Fiscal Printer : %s", msg)
        status = {"status": "unavailable", "result": False, "message": [e] or [""]}
        _logger.info(status)
    return status
