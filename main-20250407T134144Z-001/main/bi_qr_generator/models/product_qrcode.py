# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.

import qrcode
import base64
from io import BytesIO
from odoo import models, fields, api


class ProductScreenEnable(models.Model):
    _inherit = "product.template"

    name = fields.Char(string="Name")
    qr_code = fields.Char('QR Code', tracking=True, compute='_compute_qr_code', inverse='_set_qr_code', store=True)
    qr_image = fields.Binary(string="QR Image", attachment=True, store=True , compute="_compute_generate_qr_code")


    _sql_constraints = [
        ('unique_qrcode', 'unique (qr_code)', 'QR Code address already exists!')
    ]

    @api.depends('product_variant_ids.qr_code')
    def _compute_qr_code(self):
        self.qr_code = False
        for template in self:
            if len(template.product_variant_ids) == 1:
                template.qr_code = template.product_variant_ids.qr_code


    def _set_qr_code(self):
        if len(self.product_variant_ids) == 1:
            self.product_variant_ids.qr_code = self.qr_code


    @api.model_create_multi
    def create(self, vals_list):
        '''
            for autogenerate sequence in QR Code
        '''

        for value in vals_list:
            if value.get('qr_code'):
                pro['qr_code'] = value['qr_code']

            res = self.env["res.config.settings"].sudo().search([], limit=1, order="id desc").product_qr_code_generator
            if res == True:
                value['qr_code'] = self.env['ir.sequence'].next_by_code('product.template')
            pro = super(ProductScreenEnable, self).create(vals_list)
            if 'qr_code' in value:
                pro.write({'qr_code': value.get('qr_code')})
        return pro

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







