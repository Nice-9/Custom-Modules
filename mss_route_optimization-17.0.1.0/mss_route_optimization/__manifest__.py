# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.


{
    'name': 'Route Optimization',
    'version': '1.0',
    'category': '',
    'sequence': 200,
    'summary': 'Route optimization in Odoo refers to enhancing the delivery and logistics process by minimizing travel distances, time, and costs associated with managing deliveries or transportation. This feature is critical for businesses with delivery fleets or field services, as it improves efficiency and reduces operational expenses.',
    'description': """
Route optimization in Odoo refers to enhancing the delivery and logistics process by minimizing travel distances, time, and costs associated with managing deliveries or transportation. This feature is critical for businesses with delivery fleets or field services, as it improves efficiency and reduces operational expenses.
""",
    'author': 'Master Software Solutions',
    'website': 'https://www.mastersoftwaresolutions.com/',
    'depends': [
        'base', 'sale_management', 'mail', 'web_map','web','fleet','base_geolocalize'
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/traktop.xml',
        'data/cron.xml',
    ],
    'demo': [
    ],
    'images': ['static/description/main_screenshot.png', 'static/description/icon.png'],
    'installable': True,
    'application': True,
    'pre_init_hook': '',
    'license': 'LGPL-3',
    'assets': {
        'web.assets_backend': [
             'mss_route_optimization/static/src/**/*',
             'web_map/static/src/map_view/map_renderer.js',
        ],
        'web.assets_frontend': [
        ],
        'web.assets_tests': [
        ],
    }
}
