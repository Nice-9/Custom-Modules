# -*- coding: utf-8 -*-
{
    "name": "Sybyl Subscription",
    "summary": "Sybyl Subscription",
    "author": "Sybyl",
    "website": "https://www.sybyl.com",
    "category": "Uncategorized",
    "version": "0.1",
    "license": "LGPL-3",
    "depends": [
        "base",
        "sale_subscription",
        "enhanced_survey_management",
    ],
    "data": [
        "security/ir.model.access.csv",
        "views/crm_lead_views.xml",
        "views/partner_views.xml",
        "views/sale_order_views.xml",
        "views/subscription_vehicle_views.xml",
        "views/subscription_dog_views.xml",
        "views/subscription_type_views.xml",
        "views/survey_question_views.xml",
    ],
    'assets': {
        'web.assets_backend': [
            'sybyl_subscription_custom/static/src/js/list_rendere.js',
            'sybyl_subscription_custom/static/src/js/kanban_header.js',
            'sybyl_subscription_custom/static/src/js/graph_view.js',
            'sybyl_subscription_custom/static/src/js/pivot_model.js',
        ]
    },
}
