# -*- coding: utf-8 -*-

import logging

from odoo.http import request

from odoo import http, fields, _

_logger = logging.getLogger(__name__)


class PosController(http.Controller):
    @http.route(["/pos/scan_qrcode_customer"], type="json", auth="user")
    def scan_qrcode_customer(self, qr_code):
        _logger.info(qr_code)
        if qr_code:
            customer_ids = (
                request.env["res.partner"]
                .sudo()
                .search(
                    [("qr_sequence", "=", qr_code)],
                )
            )
            if not customer_ids:
                return {
                    "state": "none",
                    "customer_list": None,
                }
            all_customer_ids = customer_ids + customer_ids.child_ids
            all_customer_ids_search_read = (
                request.env["res.partner"]
                .sudo()
                .search_read(
                    [("id", "in", (customer_ids + customer_ids.child_ids).ids)],
                    fields=[
                        "id",
                        "name",
                        "title",
                        "email",
                        "phone",
                        "mobile",
                        "image_128",
                        "display_name",
                        "user_id",
                        "subscription_state",
                        "check_in_out_state",
                    ],
                )
            )
            result = all_customer_ids.filtered(
                lambda l: l.subscription_state == "active"
            )
            if not customer_ids.subscription_state:
                return {"state": "expired"}
            if all_customer_ids_search_read:
                return {
                    "state": "active",
                    "customer_list": all_customer_ids_search_read,
                }
            return {
                "state": "none",
                "customer_list": None,
            }

    @http.route(["/pos/update_customer_sign_in_out"], type="json", auth="public")
    def update_customer_sign_in_out(self, customer_checklist_dict):
        _logger.info(customer_checklist_dict)
        if customer_checklist_dict:
            for customer in customer_checklist_dict:
                partner_id = (
                    request.env["res.partner"].sudo().browse(customer.get("id"))
                )
                if customer.get("checked"):
                    partner_id.toggle_check_in_out()
                    request.env["partner.checkin.history"].sudo().toggle_check_in_out(
                        partner_id.id
                    )
                request.env["partner.checkin.log"].sudo().create(
                    {
                        "partner_id": partner_id.id,
                        "state": customer.get("checked"),
                    }
                )
            return {"state": "updated"}
        return {"state": "no_change"}
