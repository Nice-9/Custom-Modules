# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.

{
    "name": "Sign Up User Approval Process",
    "version": "17.0.0.0",
    "category": "Website",
    "summary": "Signup User Approval process user account approval process user registration approval user account approve sign up user approve process sign up user approve process user account validation process validate new user register validate new user account ",
    "description": """

        Sign up user approval in odoo,
        Admin can Approve User Account in odoo,
        Admin can Reject User Account in odoo,
        Users Gets Email Notification in odoo,
        Approved User can Easily Login into Account in odoo,
        Email Notification by Approval and rejection of Account in odoo,

    """,
    "author": "BrowseInfo",
    'price': 25,
    'currency': "EUR",
    "website": "https://www.browseinfo.com",
    "depends": ['website'],
    "data": [
        'data/mail_template.xml',
        'views/res_user.xml',
        'views/template.xml'
    ],
    'post_init_hook': '_update_internal_user_approved',
    "license": 'OPL-1',
    "auto_install": False,
    "installable": True,
    'live_test_url': 'https://youtu.be/GeYrLXMCdGE',
    "images": ['static/description/Banner.gif'],
}
