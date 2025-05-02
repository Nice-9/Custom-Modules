# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.

from odoo.http import request

from odoo import http, _
from odoo.addons.auth_signup.controllers.main import AuthSignupHome
from odoo.addons.website.controllers.main import Website


class WebsiteApproval(Website):
    # Error Message
    @http.route(website=True, auth="public", sitemap=False)
    def web_login(self, *args, **kw):
        res = super().web_login(*args, **kw)
        if res.is_qweb and res.qcontext.get("error") == "Not Approved User":
            res.qcontext["error"] = _(
                "You are already registered! Please wait for approval."
            )
        return res


class AuthSignupApproval(AuthSignupHome):
    # Error Message
    @http.route("/web/signup", type="http", auth="public", website=True, sitemap=False)
    def web_auth_signup(self, *args, **kw):
        res = super().web_auth_signup(*args, **kw)
        if res.is_qweb and res.qcontext.get("error") == "Not Approved User":
            res.qcontext["approval_msg"] = _(
                "You registered successfully! Wait for account approval."
            )
            res.qcontext["error"] = False
            approval_msg = _(
                "Thank you for registering with us. "
                "We will send you a notification as soon as your registration is verified by the Administrator."
            )

            template = request.env.ref('bi_signup_user_approval.mail_template_user_request',
                                    raise_if_not_found=False)
            users = request.env['res.users'].sudo().search([])
            admin_users = users.filtered(lambda l:l._is_system())
            if template:
                for rec in admin_users:
                    template.sudo().send_mail(rec.id, force_send=True)
            return request.render(
                "bi_signup_user_approval.signup_success_page",
                {"approval_msg": approval_msg},
            )

        return res
