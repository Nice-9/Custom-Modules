# -*- coding: utf-8 -*-
# Part of Softhealer Technologies.

from odoo import fields, models, _
import xlwt
import pytz
import base64
from datetime import timedelta
from odoo.exceptions import UserError
import io
import re


class PosDetails(models.TransientModel):
    _inherit = "pos.details.wizard"

    def generate_xls_report(self):
        workbook = xlwt.Workbook()

        # Define styles
        heading_format = xlwt.easyxf(
            "font:height 300,bold True;pattern: pattern solid, fore_colour gray25;align: horiz center"
        )
        bold = xlwt.easyxf(
            "font:bold True;pattern: pattern solid, fore_colour gray25;align: horiz left"
        )
        format1 = xlwt.easyxf("font:bold True;;align: horiz left")
        format2 = xlwt.easyxf("font:bold True")
        format3 = xlwt.easyxf("align: horiz left")

        row = 1
        date_start = self.start_date or fields.Date.context_today(self)
        date_stop = self.end_date or (date_start + timedelta(days=1, seconds=-1))

        # Ensure valid date range
        if date_stop < date_start:
            date_stop = date_start + timedelta(days=1, seconds=-1)

        config_ids = self.pos_config_ids.ids
        orders = self.env["pos.order"].search(
            [
                ("state", "in", ["paid", "invoiced", "done"]),
                ("date_order", ">=", fields.Datetime.to_string(date_start)),
                ("date_order", "<=", fields.Datetime.to_string(date_stop)),
                ("config_id", "in", config_ids),
            ]
        )

        user_currency = self.env.company.currency_id
        products_sold = {}
        taxes = {}
        total = 0.0

        payment_ids = (
            self.env["pos.payment"].search([("pos_order_id", "in", orders.ids)]).ids
        )
        if payment_ids:
            query = "SELECT id, name FROM pos_config WHERE id IN %s"
            self.env.cr.execute(query, (tuple(config_ids),))
            config_data = self.env.cr.fetchall()
            config_dict = {row[0]: row[1] for row in config_data}

            def sanitize_column_name(name):
                # Replace any sequence of non-alphanumeric characters with an underscore
                return re.sub(r'\W+', '_', name)

            sanitized_config_names = {sanitize_column_name(name): name for name in config_dict.values()}


            config_columns = ", ".join(
                [f"SUM(CASE WHEN session.config_id = {config_id} THEN amount ELSE 0 END) AS {sanitize_column_name(config_name)}"
                 for config_id, config_name in config_dict.items()]
            )

            dynamic_query = f"""
                SELECT 
                    method.name, 
                    {config_columns},
                    SUM(amount) AS total
                FROM pos_payment AS payment
                JOIN pos_payment_method AS method ON payment.payment_method_id = method.id
                JOIN pos_session AS session ON payment.session_id = session.id
                JOIN pos_config AS config ON session.config_id = config.id
                WHERE payment.id IN %s
                GROUP BY method.name
            """

            self.env.cr.execute(dynamic_query, (tuple(payment_ids),))
            results = self.env.cr.fetchall()
            columns = ['name'] + list(sanitized_config_names.keys()) + ['total']
            processed_results = []

            for row in results:
                result_dict = {}

                for col_name, value in zip(columns, row):
                    if col_name in sanitized_config_names:
                        result_dict[sanitized_config_names[col_name]] = value
                    else:
                        result_dict[col_name] = value
                processed_results.append(result_dict)

            print("Payments:", processed_results)
            payments = processed_results
        else:
            payments = []

        for order in orders:
            total += (
                order.pricelist_id.currency_id._convert(
                    order.amount_total,
                    user_currency,
                    order.company_id,
                    order.date_order or fields.Date.today(),
                )
                if user_currency != order.pricelist_id.currency_id
                else order.amount_total
            )

            currency = order.session_id.currency_id
            for line in order.lines:
                key = (
                    line.product_id.id,
                    line.price_unit,
                    line.price_subtotal,
                    line.price_subtotal_incl,
                    line.discount,
                )
                products_sold.setdefault(key, {"product": line.product_id, "qty": 0.0})
                products_sold[key]["qty"] += line.qty

                if line.tax_ids_after_fiscal_position:
                    line_taxes = line.tax_ids_after_fiscal_position.sudo().compute_all(
                        line.price_unit * (1 - (line.discount or 0.0) / 100.0),
                        currency,
                        line.qty,
                        product=line.product_id,
                        partner=line.order_id.partner_id or False,
                    )
                    for tax in line_taxes["taxes"]:
                        taxes.setdefault(
                            tax["id"],
                            {
                                "name": tax["name"],
                                "tax_amount": 0.0,
                                "base_amount": 0.0,
                            },
                        )
                        taxes[tax["id"]]["tax_amount"] += tax["amount"]
                        taxes[tax["id"]]["base_amount"] += tax["base"]
                else:
                    taxes.setdefault(
                        0,
                        {"name": _("No Taxes"), "tax_amount": 0.0, "base_amount": 0.0},
                    )
                    taxes[0]["base_amount"] += line.price_subtotal_incl

        # Aggregate products
        aggregated_products = {}
        for key, value in products_sold.items():
            product = value["product"]
            qty = value["qty"]
            price_unit = key[1]
            tax_excluded = round(key[2] * qty, 2)
            tax_included = round(key[3] * qty, 2)
            if price_unit > 0:
                qty_wrong = tax_included/price_unit
                if qty_wrong != qty:
                    answer = qty_wrong/qty
                    tax_included = tax_included/answer
                    tax_excluded = tax_excluded/answer
            discount = key[4]

            product_key = (product.id, price_unit, discount)
            if product_key in aggregated_products:
                aggregated_products[product_key]["quantity"] += qty
                aggregated_products[product_key]["tax_excluded"] += tax_excluded
                aggregated_products[product_key]["tax_included"] += tax_included
            else:
                aggregated_products[product_key] = {
                    "product_name": product.name_get()[0][1],
                    "quantity": qty,
                    "price_unit": price_unit,
                    "tax_excluded": tax_excluded,
                    "tax_included": tax_included,
                    "discount": discount,
                    "uom": product.uom_id.name,
                }

        products = sorted(aggregated_products.values(), key=lambda l: l["product_name"])

        taxes = list(taxes.values())
        worksheet = workbook.add_sheet("Excel Report")

        # Set column widths
        worksheet.col(0).width = int(25 * 320)
        worksheet.col(1).width = int(25 * 120)
        worksheet.col(2).width = int(14 * 240)
        worksheet.col(3).width = int(16 * 280)
        worksheet.col(4).width = int(15 * 300)
        worksheet.col(5).width = int(14 * 300)

        # Write headers
        worksheet.write_merge(0, 1, 0, 3, "Sale Details", heading_format)
        worksheet.write_merge(
            2,
            3,
            0,
            3,
            date_start.strftime("%d/%m/%y") + " - " + date_stop.strftime("%d/%m/%y"),
            heading_format,
        )
        worksheet.write_merge(5, 5, 0, 1, "Products", format1)
        worksheet.write(6, 0, "Product", bold)
        worksheet.write(6, 1, "Quantity", bold)
        worksheet.write(6, 2, "Price per Unit", bold)
        worksheet.write(6, 3, "Total (tax excluded)", bold)
        worksheet.write(6, 4, "Total (tax included)", bold)

        # Write product data
        row = 7
        total_tax_excluded = 0.0
        total_tax_included = 0.0
        for rec in products:
            worksheet.write(row, 0, rec.get("product_name"), format3)
            worksheet.write(row, 1, rec.get("quantity"), format3)
            worksheet.write(row, 2, rec.get("price_unit"), format3)
            total_tax_excluded += round(rec.get("tax_excluded"), 2)
            total_tax_included += round(rec.get("tax_included"), 2)
            worksheet.write(row, 3, "{:,}".format(round(rec.get("tax_excluded"), 2)), format3)
            worksheet.write(row, 4, "{:,}".format(round(rec.get("tax_included"), 2)), format3)
            row += 1

        # Write payment data
        row += 2
        worksheet.write(row,0,"Total", format2)
        worksheet.write(row,3,"{:,}".format(round(total_tax_excluded, 2)), format3)
        worksheet.write(row,4,"{:,}".format(round(total_tax_included, 2)), format3)
        row += 2
        worksheet.write_merge(row, row, 0, 1, "Payments", format1)
        row += 1
        # Example: payments is the list of dictionaries generated from the query
        # payments = [{'Gate A (Limuru)': 1182179.0, 'Gate C (Sharks)': 519135.0, ... , 'total': 2426751.0}, ...]

        # Write headers dynamically based on keys in payments
        if payments:
            headers = list(payments[0].keys())  # Assuming all dictionaries have the same keys
            for col_num, header in enumerate(headers):
                worksheet.write(row, col_num, header, bold)  # Assuming format_header is defined for header formatting

        # Write data for each row
        row += 1
        for rec in payments:
            for col_num, header in enumerate(headers):
                value = rec.get(header)
                # Check if value is numeric and round it if necessary
                if isinstance(value, (int, float)):
                    formatted_value = "{:,}".format(round(value, 2))
                    worksheet.write(row, col_num, formatted_value, format3)
                else:
                    worksheet.write(row, col_num, list(value.values())[0], format3)
            row += 1

        # Write tax data
        row += 2
        worksheet.write_merge(row, row, 0, 1, "Taxes", format1)
        row += 1
        worksheet.write(row, 0, "Name", bold)
        worksheet.write(row, 1, "Tax Amount", bold)
        worksheet.write(row, 2, "Base Amount", bold)
        row += 1
        for rec in taxes:
            worksheet.write(row, 0, rec.get("name"), format3)
            worksheet.write(row, 1, "{:,}".format(round(rec.get("tax_amount"), 2)), format3)
            worksheet.write(row, 2, "{:,}".format(round(rec.get("base_amount"), 2)), format3)
            row += 1

        # Write total
        row += 2
        worksheet.write(row, 0, "Total", bold)
        worksheet.write(row, 1, "{:,}".format(round(user_currency.round(total), 2)), bold)

        filename = "Sale Order Xls Report.xls"
        fp = io.BytesIO()
        workbook.save(fp)
        data = base64.encodebytes(fp.getvalue())

        IrAttachment = self.env["ir.attachment"]
        attachment_vals = {
            "name": filename,
            "res_model": "ir.ui.view",
            "type": "binary",
            "datas": data,
            "public": True,
        }
        fp.close()

        attachment = IrAttachment.search(
            [
                ("name", "=", filename),
                ("type", "=", "binary"),
                ("res_model", "=", "ir.ui.view"),
            ],
            limit=1,
        )
        if attachment:
            attachment.write(attachment_vals)
        else:
            attachment = IrAttachment.create(attachment_vals)

        if not attachment:
            raise UserError("There is no attachments...")

        url = "/web/content/" + str(attachment.id) + "?download=true"
        return {
            "type": "ir.actions.act_url",
            "url": url,
            "target": "new",
        }
