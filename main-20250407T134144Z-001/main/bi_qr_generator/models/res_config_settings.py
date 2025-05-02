# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.


from odoo import models, fields, api


class ResConfig(models.TransientModel):
    _inherit = 'res.config.settings'

    product_qr_code_generator = fields.Boolean(string='Generate QR Code When Product Is Create',
                                               help='Enable setting if you want to generate QR code for product at the time of creation')


    @api.model
    def get_values(self):
        conf = self.env['ir.config_parameter']
        return {
            'product_qr_code_generator': conf.get_param('ResConfig.product_qr_code_generator'),
        }

    def set_values(self):
        super(ResConfig, self).set_values()
        conf = self.env['ir.config_parameter']
        conf.set_param('ResConfig.product_qr_code_generator', self.product_qr_code_generator)
