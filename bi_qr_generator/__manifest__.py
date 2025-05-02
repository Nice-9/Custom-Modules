# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.

{
    'name': 'Generate Product QR Code',
    'version': '17.0',
    'category': 'Sales',
    'summary': 'Create Product QRCode generator product QR code generator for product generate QRCode for product variant QR code for product generate Product QRcode Generate Product QR code Auto QR code generator for product auto QRcode generator for product barcode',
    'description': """

            Product QR Code Generator in odoo,
            Generate QR Code At the Time of Product Creation in odoo,
            Generate QR Code when new Product create in odoo,
            Manually Generate QR Code in odoo,
            Manually Generate QR Code for Multiple Product in odoo,
            Product Search Based on QR code in odoo,

    """,
    'author': 'BrowseInfo',
    "price": 6,
    "currency": 'EUR',
    'website': 'https://www.browseinfo.com',
    'depends': ['base', 'product'],
    'data': [
        'security/custom_group.xml',
        'security/ir.model.access.csv',
        'views/res_config_settings.xml',
        'views/product_qrcode.xml',
        'views/product_variants_qrcode.xml',
        'data/ir_sequence_data.xml',
        'wizard/generate_qrcode.xml',
    ],
    'installable': True,
    'auto_install': False,
    "live_test_url": "https://youtu.be/BcXFdGW9pCA",
    "images":['static/description/Banner.gif'],
    'license': 'OPL-1'
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
