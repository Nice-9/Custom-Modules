# -*- coding: utf-8 -*-

from odoo import models, fields, api, _, SUPERUSER_ID
from odoo.addons.auth_signup.models.res_partner import SignupError, now


class ResUsers(models.Model):
    _inherit = "res.users"

    child_ids_store = fields.Char()

    @api.model
    def _signup_create_user(self, values):
        """signup a new user using the template user"""

        # check that uninvited users may sign up
        if "partner_id" not in values:
            if self._get_signup_invitation_scope() != "b2c":
                raise SignupError(_("Signup is not allowed for uninvited users"))
        user = self._create_user_from_template(values)
        if "child_ids_store" in values:
            child_ids = values["child_ids_store"].split(",")
            for rec in child_ids:
                partner = self.env["res.partner"].sudo().browse(int(rec))
                partner.sudo().write({"parent_id": user.partner_id.id})
        return user
