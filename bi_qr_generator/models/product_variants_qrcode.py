# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.

import qrcode
import base64
from io import BytesIO
from odoo import models, fields, api


class ProductVariants(models.Model):
    _inherit = "product.product"

    qr_code = fields.Char('QR Code')
    qr_image = fields.Binary(string="QR Image", attachment=True, store=True , compute="_compute_generate_qr_code")


    _sql_constraints = [
        ('unique_product_qrcode', 'unique (qr_code)', 'QR Code address already exists!')
    ]

    @api.depends('qr_code')
    def _compute_generate_qr_code(self):
        for record in self:
            if record.qr_code:
                qr = qrcode.QRCode(
                    version=1,
                    error_correction=qrcode.constants.ERROR_CORRECT_L,
                    box_size=10,
                    border=4,
                )
                qr.add_data(record.qr_code)
                qr.make(fit=True)
                img = qr.make_image()
                temp = BytesIO()
                img.save(temp, format="PNG")
                display_qr_image = base64.b64encode(temp.getvalue())
                record.qr_image = display_qr_image
