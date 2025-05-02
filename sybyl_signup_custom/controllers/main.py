# -*- coding: utf-8 -*-

import logging

from odoo.http import request

from odoo.addons.auth_signup.controllers.main import AuthSignupHome as Home

_logger = logging.getLogger(__name__)


class OAuthLogin(Home):
    def get_auth_signup_qcontext(self):
        result = super(OAuthLogin, self).get_auth_signup_qcontext()
        result["countries"] = request.env["res.country"].sudo().search([])
        result["states"] = request.env["res.country.state"].sudo().search([])
        return result
