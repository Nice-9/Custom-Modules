# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.

from . import model
from . import controllers


from odoo import api, SUPERUSER_ID

def _update_internal_user_approved(env):
	users = env['res.users'].sudo().search([])
	for user in users:
	    user.write({
	        'approved_user': True,
	        'first_approval_status': True
	    })