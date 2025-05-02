# -*- coding: utf-8 -*-
{
    "name": "Sybyl Signup Custom",
    "summary": "Sybyl Signup Customization",
    "author": "Sybyl",
    "website": "https://www.sybyl.com",
    "category": "Uncategorized",
    "version": "17.0.0.1",
    "license": "LGPL-3",
    "depends": [
        "auth_signup",
        "portal",
    ],
    "data": [
        "views/auth_signup_views.xml",
    ],
    "assets": {
        "web.assets_frontend": [
            "sybyl_signup_custom/static/src/js/portal.js",
            "sybyl_signup_custom/static/src/js/addrow.js",
            "sybyl_signup_custom/static/src/scss/website.ui.scss",
        ],
    },
}
