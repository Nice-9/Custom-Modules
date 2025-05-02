# -*- coding: utf-8 -*-

import base64
import logging
import xml.etree.ElementTree as ET

import pyqrcode

from odoo import fields, models, api, _

try:
    import qrcode
except ImportError:
    qrcode = None

from . import fiscal_printer
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class AccountMove(models.Model):
    _inherit = "account.move"

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

    is_fiscal_print_done = fields.Boolean(copy=False)
    is_fiscal_reprint_done = fields.Boolean("Reprint Done", copy=False, default=False)
    is_fiscal_manual_xml_cr_done = fields.Boolean(
        "XML CR Done", copy=False, default=False
    )
    reprint_count = fields.Integer(copy=False, default=0)
    fiscal_log_ids = fields.One2many("account.fiscal.log", "account_move_id")
    total_attempts = fields.Integer(copy=False)

    xml_packet = fields.Text(compute="_compute_xml_packet")
    fiscal_receipt_no = fields.Char("Fiscal Receipt Number", copy=False)
    cus_no = fields.Char("CUSN", copy=False)
    cui_no = fields.Char("CUIN", copy=False)
    is_fiscal = fields.Boolean("Fiscal/Non-Fiscal", copy=False, readonly=True)
    is_non_kenya = fields.Boolean(default=False)

    kra_url = fields.Char(compute=_kra_url)
    kra_qr_svg_file_name = fields.Char(compute="_compute_image")
    kra_qr_png_file_name = fields.Char(compute="_compute_image")
    kra_qr_svg_image = fields.Binary("KRA QR (SVG Format)", compute="_compute_image")
    kra_qr_png_image = fields.Binary("KRA QR (PNG Format)", compute="_compute_image")

    reversed_receipt_number = fields.Char("Reverse Receipt Number", copy=False)
    pos_kra_qr_svg_image = fields.Binary(
        related="pos_order_ids.kra_qr_svg_image", string="POS KRA QR"
    )

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

    def action_fetch_qr_invoice_number(self):
        for record in self:
            esd_printer_ip_address = self.company_id.esd_printer_ip_address
            # <packet><info action="receipt" trader_sys_number_EX="123/236"></info></packet>
            # packets = ("""<packet><info action="last_receipt"></info></packet>"""
            packets = (
                """<packet><info action="receipt" receipt_number="%s"></info></packet>"""
                % record.fiscal_receipt_no
            )
            fiscal_printer.print_xml_file(
                printer_ip_address=esd_printer_ip_address,
                packets=packets,
                record_id=record,
                user_id=record.user_id,
                response_type="fetch_receipt",
                print_type="account",
            )

    def action_duplicate_receipt_print(self):
        for record in self:
            esd_printer_ip_address = self.company_id.esd_printer_ip_address
            packets = (
                """<packet><report type="protectedmemory" from="%s" to="%s" kind="receipt"></report></packet>"""
                % (record.fiscal_receipt_no, record.fiscal_receipt_no)
            )
            fiscal_printer.print_xml_file(
                printer_ip_address=esd_printer_ip_address,
                packets=packets,
                record_id=record,
                user_id=record.user_id,
                response_type="fetch_receipt",
                print_type="account",
            )

    def resend_xml_for_account_move(self):
        for record in self:
            _logger.info("Account Move ESD - Reprinting...")
            record.send_xml_for_account_move()
            record.is_fiscal_reprint_done = True
            record.reprint_count += 1

    def send_xml_for_account_move(self):
        esd_printer_ip_address = self.company_id.esd_printer_ip_address
        # if self.manual_currency_rate_active:
        #     ctx = self.env.context.copy()
        #     ctx["manual_currency_rate"] = self.manual_currency_rate
        #     self = self.with_context(ctx)
        if self.move_type == "out_invoice":
            packets = self.generate_xml_for_account_move()
        elif self.move_type == "out_refund":
            packets = self.generate_return_xml_for_account_move()
        else:
            # Reset to Draft scenario
            # packets = self.generate_return_xml_for_account_move()
            return False
        fiscal_printer.print_xml_file(
            printer_ip_address=esd_printer_ip_address,
            packets=packets,
            record_id=self,
            user_id=self.user_id,
            response_type="fetch_receipt",
            print_type="account",
        )

    def generate_xml_for_account_move(self):
        _logger.info("Account Move XML Generation")
        amount_total = 0
        account_reference = fiscal_printer.clean_string(self.name, 12)
        formatted_invoice_date = self.invoice_date.strftime("%Y-%m-%d")
        packet = ET.Element("packet")
        ET.SubElement(
            packet,
            "receipt",
            {
                "action": "begin",
                "mode": "online",
                "pharmaceutical": "no",
                "type": "tax_invoice",
                "trader_sys_number": account_reference,
                "trader_sys_number_EX": account_reference,
                "selldate": formatted_invoice_date,
                **({"nip": self.partner_id.vat} if self.partner_id.vat else {}),
                # "exemption_number": "",
            },
        )
        # Product line ids
        total_quantity = sum(
            x for x in self.invoice_line_ids.mapped("quantity") if x > 0
        )
        down_payment_quantity = 0
        down_payment_price_unit = 0
        for line in self.invoice_line_ids:
            if line.quantity < 0:
                # Finding Down payment
                deposit_product = (
                    self.env["product.product"]
                    .browse(
                        int(
                            self.env["ir.config_parameter"]
                            .sudo()
                            .get_param("sale.default_deposit_product_id")
                        )
                    )
                    .exists()
                )
                down_payment_quantity += line.quantity
                down_payment_price_unit += line.price_unit
        down_payment_price_unit_each = down_payment_price_unit / total_quantity

        # Product line ids
        for line in self.invoice_line_ids:
            if line.quantity < 0:
                continue
            if not line.product_id:
                # Ignore if no product is added, this is to ignore section in account move line
                continue
            # Taking each product and printing its details.
            # VAT codes as per tax type:
            # A = 16%, B = 8%, C = 0% and D = EX
            # TODO Need to change this fiscal_ptu_value logic
            if self.partner_id and self.partner_id.is_vat_exempted:
                ptu = (
                    self.company_id.esd_exemption_tax_id.fiscal_ptu_value
                    if self.company_id.esd_exemption_tax_id
                    else "C"
                )
            elif line.tax_ids:
                if not line.tax_ids.fiscal_ptu_value:
                    raise ValidationError(
                        _("Please Update PTU Value of the Tax related to Product")
                    )
                ptu = line.tax_ids.fiscal_ptu_value
            else:
                raise ValidationError(
                    _("Please Update Tax to Product in Invoice Lines")
                )
                # ptu = "D"
            # if line.product_id.factor_type == "taxable":
            # elif line.product_id.factor_type == "zero":
            #     ptu = "C"
            # else:
            #     ptu = "D"
            # Finding each price using total with inclusive/exclusive of tax
            # if not self.env.user.has_group("account.group_show_line_subtotals_tax_excluded"):
            #     sub_total = line.price_subtotal
            # else:
            sub_total = line.price_total
            price_unit = round(sub_total / line.quantity, 2)

            discount = line.discount
            # if line.currency_id.symbol != "KSh":
            #     # Convert non kenya currency to Kenya currency to send invoice request to KRA printer.
            #     date = fields.Date.context_today(self)
            #     convert_currency = self.env.ref("base.KES")
            #     price_unit = line.currency_id._convert(price_unit, convert_currency, line.company_id, date)
            #     discount = line.currency_id._convert(discount, convert_currency, line.company_id, date)
            sub_total = price_unit * line.quantity
            amount_total += sub_total
            if line.product_id.default_code != "DISC":
                plu = ""
                # plu – goods code ((@ - if code is to be a QR– code, # - if code is to be a barcode),
                # if line.product_id.barcode:
                #     plu = "#" + line.product_id.barcode
                full_product_name = line.product_id.name
                full_product_alpha = fiscal_printer.sanitize_and_trim(full_product_name)
                trimmed_product_name = (
                    (full_product_alpha[:40])
                    if len(full_product_alpha) > 40
                    else full_product_alpha
                )
                if self.partner_id and self.partner_id.is_vat_exempted:
                    hscode_index = (
                        self.company_id.esd_exemption_hs_code
                        if self.company_id.esd_exemption_hs_code
                        else "0001.12.00"
                    )
                elif line.product_id.hscode_index:
                    hscode_index = str(line.product_id.hscode_index)
                else:
                    hscode_index = ""

                item = ET.SubElement(
                    packet,
                    "item",
                    {
                        "name": str(trimmed_product_name),
                        "hscode_index": hscode_index,
                        "quantity": str(line.quantity),
                        "quantityunit": str(line.product_uom_id.display_name),
                        "ptu": ptu,
                        "price": fiscal_printer.format_float(price_unit),
                        "total": fiscal_printer.format_float(sub_total),
                        "action": "sale",
                        "recipe": "",
                        "charge": "",
                        "plu": plu,
                        "description": "",
                        # "description": line.product_id.description if line.product_id.description else "",
                    },
                )
                # Printing discount of that each product from order lines.
                if line.discount:
                    ET.SubElement(
                        item,
                        "discount",
                        {
                            "value": str(discount) + "%",
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
                        "value": fiscal_printer.format_float(price_unit),
                        "name": "Occasional",
                        "descid": "1",
                        "action": "discount",
                    },
                )
        # Add payment method in packet
        for payment_id in self.payment_id:
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
        amount_total = round(amount_total, 2)
        # To show the total of receipt and Cashier name, this is closing of receipt.
        ET.SubElement(
            packet,
            "receipt",
            {
                "action": "close",
                "system_number": "123456",
                "cashbox_number": "1",
                # "cashier": str(self.env.user.display_name),
                "total": fiscal_printer.format_float(amount_total),
            },
        )
        packt = ET.tostring(packet)
        _logger.info(packt)
        return packt

    def sent_return_xml_account_move(self):
        # this is used to send same XML with relevant_receipt_number and type="credit_note_item"
        _logger.info(
            "Account Move XML Generation - Credit Note Return XML Manual----------"
        )
        data = self.fiscal_log_ids[0].name
        root = ET.fromstring(data)
        sh = root.find("receipt")
        sh.set("relevant_receipt_number", str(self.fiscal_receipt_no))
        sh.set("type", "credit_note_item")
        packets = ET.tostring(root)
        esd_printer_ip_address = (
            self.env["ir.config_parameter"]
            .sudo()
            .get_param("account.esd_printer_ip_address")
        )
        fiscal_printer.print_xml_file(
            printer_ip_address=esd_printer_ip_address,
            packets=packets,
            record_id=self,
            user_id=self.user_id,
            response_type="enq",
        )

    def generate_return_xml_for_account_move(self):
        _logger.info("Account Move XML Generation - Credit Note Return")
        amount_total = 0
        packet = ET.Element("packet")
        reversed_id = (
            self.reversed_entry_id if self.reversed_entry_id else self.reversal_move_id
        )
        if self.ref and reversed_id and not reversed_id.fiscal_receipt_no:
            raise ValidationError(
                _(
                    "Please Update the 'Fiscal Receipt Number'. \n Account Move : "
                    + str(reversed_id.display_name)
                )
            )
        relevant_receipt_number = reversed_id.fiscal_receipt_no if reversed_id else ""
        if not relevant_receipt_number:
            if self.reversed_receipt_number:
                relevant_receipt_number = self.reversed_receipt_number
            else:
                raise ValidationError(
                    _(
                        "Please Update the 'Reverse Order Receipt Number' in 'Other Info'"
                    )
                )
        _logger.info("relevant_receipt_number : %s", relevant_receipt_number)
        formatted_invoice_date = self.invoice_date.strftime("%Y-%m-%d")
        ET.SubElement(
            packet,
            "receipt",
            {
                "action": "begin",
                "mode": "online",
                "pharmaceutical": "no",
                "relevant_receipt_number": relevant_receipt_number,
                "type": "credit_note_item",
                "selldate": formatted_invoice_date,
            },
        )
        # Product line ids
        for line in self.invoice_line_ids:
            if not line.product_id:
                # Ignore if no product is added, this is to ignore section in account move line
                continue
            # Taking each product and printing its details.
            # VAT codes as per tax type:
            # A = 16%, B = 8%, C = 0% and D = EX
            # TODO Need to change this fiscal_ptu_value logic
            if self.partner_id and self.partner_id.is_vat_exempted:
                ptu = (
                    self.company_id.esd_exemption_tax_id.fiscal_ptu_value
                    if self.company_id.esd_exemption_tax_id
                    else "C"
                )
            elif line.tax_ids:
                if not line.tax_ids.fiscal_ptu_value:
                    raise ValidationError(
                        _("Please Update PTU Value of the Tax related to Product")
                    )
                ptu = line.tax_ids.fiscal_ptu_value
            else:
                raise ValidationError(
                    _("Please Update Tax to Product in Invoice Lines")
                )
                # ptu = "D"
            # if line.product_id.factor_type == "taxable":
            # elif line.product_id.factor_type == "zero":
            #     ptu = "C"
            # else:
            #     ptu = "D"
            price_unit = line.price_unit
            if price_unit == 0:
                continue
            # Finding each price using total with inclusive/exclusive of tax
            # if not self.env.user.has_group("account.group_show_line_subtotals_tax_excluded"):
            #     sub_total = line.price_subtotal
            # else:
            sub_total = line.price_total
            price_unit = round(sub_total / line.quantity, 2)

            discount = line.discount
            # if line.currency_id.symbol != "KSh":
            #     # Convert non kenya currency to Kenya currency to send invoice request to KRA printer.
            #     date = fields.Date.context_today(self)
            #     convert_currency = self.env.ref("base.KES")
            #     price_unit = line.currency_id._convert(price_unit, convert_currency, line.company_id, date)
            #     discount = line.currency_id._convert(discount, convert_currency, line.company_id, date)
            sub_total = price_unit * line.quantity
            amount_total += sub_total
            if line.product_id.default_code != "DISC":
                plu = ""
                # plu – goods code ((@ - if code is to be a QR– code, # - if code is to be a barcode),
                # if line.product_id.barcode:
                #     plu = "#" + line.product_id.barcode
                if line.price_unit == 0:
                    continue
                full_product_name = line.product_id.name
                full_product_alpha = fiscal_printer.sanitize_and_trim(full_product_name)
                trimmed_product_name = (
                    (full_product_alpha[:40])
                    if len(full_product_alpha) > 40
                    else full_product_alpha
                )

                if self.partner_id and self.partner_id.is_vat_exempted:
                    hscode_index = (
                        self.company_id.esd_exemption_hs_code
                        if self.company_id.esd_exemption_hs_code
                        else "0001.12.00"
                    )
                elif line.product_id.hscode_index:
                    hscode_index = str(line.product_id.hscode_index)
                else:
                    hscode_index = ""

                item = ET.SubElement(
                    packet,
                    "item",
                    {
                        "name": str(trimmed_product_name),
                        "hscode_index": hscode_index,
                        "quantity": str(line.quantity),
                        "quantityunit": str(line.product_uom_id.display_name),
                        "ptu": ptu,
                        "price": fiscal_printer.format_float(price_unit),
                        "total": fiscal_printer.format_float(sub_total),
                        "action": "sale",
                        "recipe": "",
                        "charge": "",
                        "plu": plu,
                        "description": "",
                        # "description": line.product_id.description if line.product_id.description else "",
                    },
                )
                # Printing discount of that each product from order lines.
                if discount:
                    ET.SubElement(
                        item,
                        "discount",
                        {
                            "value": str(discount) + "%",
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
                        "value": fiscal_printer.format_float(price_unit),
                        "name": "Occasional",
                        "descid": "1",
                        "action": "discount",
                    },
                )
        # Add payment method in packet
        for payment_id in self.payment_id:
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
        receipt_close = ET.SubElement(
            packet,
            "receipt",
            {
                "action": "close",
                "system_number": "123456",
                "cashbox_number": "1",
                "cashier": str(self.env.user.display_name),
                "total": fiscal_printer.format_float(amount_total),
            },
        )
        packt = ET.tostring(packet)
        _logger.info(packt)
        return packt

    def sent_return_manual_xml_account_move(self):
        # this is used to send same XML with relevant_receipt_number and type="credit_note_item"
        _logger.info(
            "Account Move XML Generation - Credit Note Return XML Manual----------"
        )
        for fiscal_log_id in self.fiscal_log_ids:
            if not fiscal_log_id.fiscal_receipt_no:
                continue
            if self.is_fiscal_manual_xml_cr_done:
                continue
            _logger.info(fiscal_log_id)
            data = fiscal_log_id.name
            root = ET.fromstring(data)
            sh = root.find("receipt")
            sh.set("relevant_receipt_number", str(self.fiscal_receipt_no))
            sh.set("type", "credit_note_item")
            packets = ET.tostring(root)
            esd_printer_ip_address = self.company_id.esd_printer_ip_address
            fiscal_printer.print_xml_file(
                printer_ip_address=esd_printer_ip_address,
                packets=packets,
                record_id=self,
                user_id=self.user_id,
                response_type="enq",
            )
            self.is_fiscal_manual_xml_cr_done = True

    @api.model_create_multi
    def create(self, vals):
        results = super(AccountMove, self).create(vals)
        for res in results:
            if res.move_type == "out_refund":
                try:
                    if res.env.context.get("create_move_from_wizard"):
                        res.send_xml_for_account_move()
                except Exception as ex:
                    _logger.error("Error caught during request creation", exc_info=True)
                    _logger.error("Unexpected ", ex, ":", repr(str(ex)))
        return results

    def is_esd_printer_enabled(self):
        is_esd_printer_enabled = self.company_id.is_esd_printer_enabled
        if (
            is_esd_printer_enabled
            and self.company_id
            and self.company_id.country_id
            and self.company_id.country_id.code == "KE"
        ):
            return True
        else:
            self.is_non_kenya = True
            return False

    def action_post(self):
        res = super(AccountMove, self).action_post()
        # To ensure it only sending print via Invoice (out_invoice) and Credit Note (out_refund).
        # Also, To ignore Vendor Bill (in_invoice)
        if self.is_esd_printer_enabled():
            _logger.info("Action Post - move_type : %s", self.move_type)
            if self.move_type in ["out_invoice"]:
                self.send_xml_for_account_move()
            elif self.move_type == "out_refund" and not self.is_fiscal_print_done:
                # This is the ensure this is partial refund invoice and no fiscal print done.
                self.send_xml_for_account_move()
        return res

    def cron_account_move_fiscal_printer(self):
        # Fiscal print not yet done
        account_move_ids = self.search(
            [
                ("is_fiscal_print_done", "=", False),
                ("state", "=", "posted"),
                ("move_type", "=", "out_invoice"),
                ("is_non_kenya", "=", False),
            ],
            limit=10,
        )
        # Fiscal print done but no receipt
        # account_move_ids += self.search([
        #     ("fiscal_receipt_no", "=", False),
        #     ("is_fiscal_print_done", "=", True),
        #     ("state", "=", "posted"),
        #     ("move_type", "=", "out_invoice"),
        #     ("is_non_kenya", "=", False),
        # ], limit=10)
        _logger.info("Cron:- Account Move Count : %s", len(account_move_ids))
        for account_move_id in account_move_ids:
            if account_move_id.is_esd_printer_enabled():
                account_move_id.send_xml_for_account_move()

    def button_draft(self):
        res = super(AccountMove, self).button_draft()
        # While Reset to Draft, Reset Fiscal printer information to enable printing
        is_esd_printer_enabled = self.company_id.is_esd_printer_enabled
        if is_esd_printer_enabled and self.move_type in ["out_invoice", "out_refund"]:
            _logger.info("Reset to Draft - move_type : %s", self.move_type)
            # TODO: Need to confirm that Reset to Draft need to send Credit Note to KRA
            # self.send_xml_for_account_move()
        # self.write({
        #     "total_attempts": 0,
        #     "is_fiscal_print_done": 0,
        #     "is_fiscal": 0,
        # })
        return res
