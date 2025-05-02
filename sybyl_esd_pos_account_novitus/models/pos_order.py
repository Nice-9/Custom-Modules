# -*- coding: utf-8 -*-
import logging
import xml.etree.ElementTree as ET

from odoo.exceptions import ValidationError

from odoo import api, fields, models, _
from . import fiscal_printer

_logger = logging.getLogger(__name__)
import pyqrcode
import base64


def format_float(value):
    result = "{:.2f}".format(abs(value))
    return result


class PosOrder(models.Model):
    _inherit = "pos.order"

    def return_data(self, name):
        if name:
            order = self.search([("pos_reference", "=", name["name"])])
            if order:
                for rec in order:
                    return (
                        rec.fiscal_receipt_no,
                        rec.kra_qr_png_image or False,
                        rec.cus_no,
                    )
            return False, False, False
        return False, False, False
        # customer_checklist_dict.get('customer_checklist_dict'):

    @api.depends("fiscal_log_ids")
    def _kra_url(self):
        for record in self:
            if record.fiscal_log_ids:
                fiscal_log_ids = record.fiscal_log_ids.search(
                    [
                        ("id", "in", record.fiscal_log_ids.ids),
                        ("kra_url", "!=", False),
                    ],
                    limit=1,
                    order="id desc",
                )
                record.kra_url = fiscal_log_ids.kra_url
            else:
                record.kra_url = ""

    fiscal_log_ids = fields.One2many("fiscal.log", "pos_order_id")
    is_fiscal_print_done = fields.Boolean(copy=False)
    xml_packet = fields.Text(compute="_compute_xml_packet")
    fiscal_receipt_no = fields.Char("Fiscal Receipt Number", copy=False)
    is_fiscal = fields.Boolean(copy=False)
    total_attempts = fields.Integer(copy=False)

    kra_url = fields.Char(compute=_kra_url)
    kra_qr_svg_file_name = fields.Char(compute="_compute_image")
    kra_qr_png_file_name = fields.Char(compute="_compute_image")
    kra_qr_svg_image = fields.Binary("KRA QR (SVG Format)", compute="_compute_image")
    kra_qr_png_image = fields.Binary("KRA QR (PNG Format)", compute="_compute_image")

    reversed_receipt_number = fields.Char("Reverse Receipt Number", copy=False)
    cus_no = fields.Char("CUSN", copy=False)
    cui_no = fields.Char("CUIN", copy=False)

    @api.depends("kra_url")
    def _compute_image(self):
        for record in self:
            if record.kra_url:
                _logger.info("Generate QR : KRA QR Generation Initiated")
                _logger.info(
                    "Generate QR : Account Invoice Id - "
                    + str(record.id)
                    + " URL : "
                    + record.kra_url
                )
                qr_url = pyqrcode.create(record.kra_url)

                # Set folder location and filename
                folder_name = "/tmp/"
                file_name = "qr_image_" + str(record.fiscal_receipt_no)
                qr_file_location = folder_name + file_name

                _logger.info("Generate QR : Create and save the SVG & PNG file")
                qr_url.svg("%s.svg" % qr_file_location, scale=8)
                qr_url.png("%s.png" % qr_file_location, scale=6)

                _logger.info("Generate QR : QR Image created and stored in /tmp/")
                svg_file_location = "%s.svg" % qr_file_location
                png_file_location = "%s.png" % qr_file_location
                svg_out = base64.b64encode(open(svg_file_location, "rb").read())
                png_out = base64.b64encode(open(png_file_location, "rb").read())

                record.kra_qr_svg_file_name = file_name + ".svg"
                record.kra_qr_png_file_name = file_name + ".png"
                record.kra_qr_svg_image = svg_out
                record.kra_qr_png_image = png_out
                # _logger.info("Generate QR : Removing created file from /tmp/")
                # os.remove(svg_file_location)
                # os.remove(png_file_location)
                _logger.info("Generate QR : compute completed")
            else:
                record.kra_qr_svg_file_name = "none.svg"
                record.kra_qr_png_file_name = "none.png"
                record.kra_qr_svg_image = ""
                record.kra_qr_png_image = ""

    def _compute_xml_packet(self):
        for record in self:
            record = record.with_context(compute=True)
            if record.amount_total > 0:
                record.xml_packet = record.generate_xml_for_pos()
            else:
                record.xml_packet = record.generate_return_xml_for_pos()

    def action_update_fiscal_receipt_number(self):
        for record in self:
            if (
                record.config_id.pos_esd_devices
                and record.config_id.iface_fiscal_printer_ip_address
            ):
                # Check ESD device is enabled and IP is configured for this POS shop
                if not record.fiscal_receipt_no and record.fiscal_log_ids:
                    # Already Fiscal Receipt exists, try to fetch receipt no. only from KRA
                    record.fiscal_log_ids[0].get_receipt_no()
                if not record.fiscal_receipt_no or record.fiscal_receipt_no == "0":
                    # If receipt no is empty or zero then it wasn't registered in KRA yet, so register the Order
                    record.send_xml_for_pos()

    def send_xml_for_pos(self):
        for record in self:
            record = record.with_context(send_xml=True)
            if record.amount_total > 0:
                packets = record.generate_xml_for_pos()
            else:
                packets = record.generate_return_xml_for_pos()
            fiscal_printer.print_xml_file(
                printer_ip_address=record.config_id.iface_fiscal_printer_ip_address,
                packets=packets,
                record_id=record,
                session_id=record.session_id,
                user_id=record.user_id,
                response_type="fetch_receipt",
                print_type="pos",
            )

    def generate_xml_for_pos(self):
        _logger.info("POS Order")
        total = 0
        pos_reference = fiscal_printer.clean_string(self.pos_reference, 12)
        formatted_date_order = self.date_order.strftime("%Y-%m-%d")
        packet = ET.Element("packet")
        ET.SubElement(
            packet,
            "receipt",
            {
                "action": "begin",
                "mode": "online",
                "pharmaceutical": "no",
                "type": "tax_invoice",
                "trader_sys_number": pos_reference,
                "trader_sys_number_EX": pos_reference,
                "selldate": formatted_date_order,
                # "nip": "",
                # "exemption_number": "",
            },
        )
        for line in self.lines:
            # Taking each product and printing its details.
            # VAT codes as per tax type:
            # A = 16%, B = 8%, C = 0% and D = EX
            if line.product_id.factor_type == "taxable":
                if line.tax_ids:
                    if not line.tax_ids.fiscal_ptu_value:
                        raise ValidationError(
                            _("Please Update PTU Value of the Taxes related to Product")
                        )
                    ptu = line.tax_ids.fiscal_ptu_value
                else:
                    ptu = "D"
            elif line.product_id.factor_type == "zero":
                ptu = "C"
            else:
                ptu = "D"
            if line.product_id.default_code != "DISC":
                plu = ""
                # plu – goods code ((@ - if code is to be a QR– code, # - if code is to be a barcode),
                sub_total = line.price_unit * line.qty
                total += sub_total
                full_product_name = fiscal_printer.sanitize_and_trim(
                    line.full_product_name
                )
                trimmed_product_name = fiscal_printer.trim_product_name(
                    full_product_name
                )
                item = ET.SubElement(
                    packet,
                    "item",
                    {
                        "name": str(trimmed_product_name),
                        "hscode_index": (
                            str(line.product_id.hscode_index)
                            if line.product_id.hscode_index
                            else ""
                        ),
                        "quantity": str(line.qty),
                        "quantityunit": str(line.product_uom_id.display_name),
                        "ptu": ptu,
                        "price": fiscal_printer.format_float(line.price_unit),
                        "total": fiscal_printer.format_float(sub_total),
                        "action": "sale",
                        "recipe": "",
                        "charge": "",
                        "plu": plu,
                        "description": "",
                        # 'description': line.product_id.description if line.product_id.description else "",
                    },
                )
                # Printing discount of that each product from order lines.
                if line.discount:
                    ET.SubElement(
                        item,
                        "discount",
                        {
                            "value": str(line.discount) + "%",
                            "name": "Occasional",
                            "descid": "1",
                            "action": "discount",
                        },
                    )
            if line.product_id.default_code == "DISC":
                ET.SubElement(
                    packet,
                    "discount",
                    {
                        "value": fiscal_printer.format_float(line.price_unit),
                        "name": "Occasional",
                        "descid": "1",
                        "action": "discount",
                    },
                )
        # Add payment method in packet
        for payment_id in self.payment_ids:
            # 1. type = „card”,
            # 2. type = „cheque”,
            # 3. type = „voucher”, (on printout „Token”),
            # 4. type = „credit”,
            # 5. type = „transfer”,
            # 6. type = „customer_account”,
            # 7. type = „foreign_currency”,
            # 8. type = „cash”,
            # 9. type = „mobile”
            # 10. type = „token”, (on printout „ Voucher”),
            if payment_id.amount > 0:
                ET.SubElement(
                    packet,
                    "payment",
                    {
                        "type": payment_id.payment_method_id.fiscal_printer_payment_type,
                        "action": "add",
                        "value": fiscal_printer.format_float(payment_id.amount),
                        "mode": "payment",
                        "name": payment_id.payment_method_id.display_name,
                    },
                )
        # To show the total of receipt and Cashier name, this is closing of receipt.
        ET.SubElement(
            packet,
            "receipt",
            {
                "action": "close",
                "systemno": str(self.config_id.id),
                "cashier": str(self.cashier),
                "total": fiscal_printer.format_float(self.amount_total),
            },
        )
        ET.SubElement(
            packet,
            "error",
            {
                "action": "get",
                "value": "",
            },
        )
        packt = ET.tostring(packet)
        return packt

    def generate_return_xml_for_pos(self):
        _logger.info("Return Order")
        total = 0
        packet = ET.Element("packet")
        if self.refunded_order_ids and not self.refunded_order_ids[0].fiscal_receipt_no:
            raise ValidationError(
                _(
                    "Please Update the 'Fiscal Receipt Number'. \n POS order : "
                    + str(self.refunded_order_ids[0].pos_reference)
                )
            )
        relevant_receipt_number = (
            self.refunded_order_ids[0].fiscal_receipt_no
            if self.refunded_order_ids
            else ""
        )
        pos_reference = fiscal_printer.sanitize_and_trim(self.pos_reference)
        ET.SubElement(
            packet,
            "receipt",
            {
                "action": "begin",
                "mode": "online",
                "pharmaceutical": "no",
                "relevant_receipt_number": relevant_receipt_number,
                "type": "credit_note_item",
            },
        )
        for line in self.lines:
            # Taking each product and printing its details.
            # VAT codes as per tax type:
            # A = 16%, B = 8%, C = 0% and D = EX
            if line.product_id.factor_type == "taxable":
                if line.tax_ids:
                    ptu = line.tax_ids.fiscal_ptu_value
                else:
                    ptu = "D"
            elif line.product_id.factor_type == "zero":
                ptu = "C"
            else:
                ptu = "D"
            if line.product_id.default_code != "DISC":
                plu = ""
                # plu – goods code ((@ - if code is to be a QR– code, # - if code is to be a barcode),
                if line.product_id.barcode:
                    plu = "#" + line.product_id.barcode
                sub_total = line.price_unit * line.qty
                total += sub_total
                full_product_name = fiscal_printer.sanitize_and_trim(
                    line.full_product_name
                )
                trimmed_product_name = fiscal_printer.trim_product_name(
                    full_product_name
                )
                item = ET.SubElement(
                    packet,
                    "item",
                    {
                        "name": str(trimmed_product_name),
                        "hscode_index": (
                            str(line.product_id.hscode_index)
                            if line.product_id.hscode_index
                            else ""
                        ),
                        "quantity": fiscal_printer.format_float(line.qty),
                        "quantityunit": str(line.product_uom_id.display_name),
                        "ptu": ptu,
                        "price": fiscal_printer.format_float(line.price_unit),
                        # "total": fiscal_printer.format_float(sub_total),
                        "action": "sale",
                        "recipe": "",
                        "charge": "",
                        "plu": plu,
                        "description": "",
                        # 'description': line.product_id.description if line.product_id.description else "",
                    },
                )
                # Printing discount of that each product from order lines.
                if line.discount:
                    ET.SubElement(
                        item,
                        "discount",
                        {
                            "value": str(line.discount) + "%",
                            "name": "Occasional",
                            "descid": "1",
                            "action": "discount",
                        },
                    )
            if line.product_id.default_code == "DISC":
                ET.SubElement(
                    packet,
                    "discount",
                    {
                        "value": fiscal_printer.format_float(line.price_unit),
                        "name": "Occasional",
                        "descid": "1",
                        "action": "discount",
                    },
                )
        # Add payment method in packet
        # for payment_id in self.payment_ids:
        #     ET.SubElement(packet, "payment", {
        #         "type": payment_id.payment_method_id.fiscal_printer_payment_type,
        #         "action": "add",
        #         "value": fiscal_printer.format_float(payment_id.amount),
        #         "mode": "payment",
        #         "name": payment_id.payment_method_id.display_name,
        #     })
        # To show the total of receipt and Cashier name, this is closing of receipt.
        ET.SubElement(
            packet,
            "receipt",
            {
                "action": "close",
                "system_number": str(self.config_id.id) or "123456",
                "cashier": str(self.cashier),
                "total": fiscal_printer.format_float(self.amount_total),
            },
        )
        ET.SubElement(
            packet,
            "error",
            {
                "action": "get",
                "value": "",
            },
        )
        packt = ET.tostring(packet)
        return packt

    @api.model
    def _process_order(self, order, draft, existing_order):
        res = super(PosOrder, self)._process_order(order, draft, existing_order)
        # if order.get("data") and order.get("data").get("amount_total") == 0:
        #     raise UserError("Order with Zero is not allowed")
        try:
            self.browse(res).send_xml_for_pos()
        except Exception as e:
            _logger.error(e)
        return res

    @api.model
    def _order_fields(self, ui_order):
        order_fields = super(PosOrder, self)._order_fields(ui_order)
        order_fields.update(
            {
                "fiscal_receipt_no": ui_order.get("fiscal_receipt_no"),
                "kra_qr_png_image": ui_order.get("kra_qr_png_image"),
            }
        )
        return order_fields

    def _export_for_ui(self, order):
        result = super(PosOrder, self)._export_for_ui(order)
        result.update(
            {
                "fiscal_receipt_no": order.fiscal_receipt_no,
                "kra_qr_png_image": order.kra_qr_png_image,
            }
        )
        return result
