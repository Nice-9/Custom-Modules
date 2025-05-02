# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.
{
    "name": "POS Mobile Barcode and QR Code Scanner",
    "version": "17.0.0.0",
    "category": "Point of Sale",
    'summary': 'POS Barcode Scanner POS QR Code Scanner POS Mobile Barcode Scanner POS Mobile QRCode Scanner Point Of Sale Mobile Barcode Scanner Point Of Sale Mobile QRCode Scanner point of sale barcode scanner pos scanner pos product scanner pos product barcode scanner',
    "description": """
    
        POS Mobile Barcode Scanner in odoo,
        POS Mobile QRCode Scanner in odoo,
        POS Barcode and QR Code Scanner with Mobile in odoo,
        Continue Scan Product in odoo,
        Product Scan with Mobile in odoo,
        Success Scan Notification in odoo,
        Failed Scan Notification in odoo,
        Success Scan Play Sound in odoo,
        Failed Scan Play Sound in odoo,
        Scan Product with Image in odoo,
    
    """,
    'author': 'BrowseInfo',
    "price": 45,
    "currency": 'EUR',
    'website': 'https://www.browseinfo.com',
    "depends": [
        'point_of_sale',
        'bi_qr_generator',
        'customer_product_qrcode',
        'sale_subscription',
        'sybyl_subscription_custom',
        'contacts'
    ],
    "data": [
        'security/ir.model.access.csv',

        'data/ir_cron.xml',
        'views/pos_config_view.xml',
        'views/res_partner_views.xml',
    ],
    'assets': {
        'point_of_sale._assets_pos': [
            'bi_pos_scan_mobile_barcode/static/src/css/iao-alert.css',

            'bi_pos_scan_mobile_barcode/static/src/js/iao-alert.jquery.js',
            'bi_pos_scan_mobile_barcode/static/src/js/pos_db.js',
            'bi_pos_scan_mobile_barcode/static/src/js/posStore.js',
            'bi_pos_scan_mobile_barcode/static/src/js/models.js',

            'bi_pos_scan_mobile_barcode/static/src/js/QRButton.js',
            'bi_pos_scan_mobile_barcode/static/src/js/scanqrcode.js',
            'bi_pos_scan_mobile_barcode/static/src/js/scanqrcodecustomer.js',
            'bi_pos_scan_mobile_barcode/static/src/js/customerListPopup.js',
            'bi_pos_scan_mobile_barcode/static/src/js/customerListPopupExtend.js',
            'bi_pos_scan_mobile_barcode/static/src/js/subscriptionListView.js',

            'bi_pos_scan_mobile_barcode/static/src/xml/**/*',
            # 'bi_pos_scan_mobile_barcode/static/src/qr-scanner/src/qr-scanner.ts',
            'https://cdnjs.cloudflare.com/ajax/libs/font-awesome/5.15.3/css/all.min.css',
        ],
    },
    'license': 'OPL-1',
    "auto_install": False,
    "installable": True,
    "live_test_url": 'https://youtu.be/xGSY3Zelq3U',
    "images": ["static/description/Banner.gif"],
}
