# -*- coding: utf-8 -*-
################################################################################
#
#    Kolpolok Ltd. (https://www.kolpolok.com)
#    Author: Kaushik Ahmed Apu, Zarin Tasnim, Aqil Mahmud(<https://www.kolpolok.com>)
#
################################################################################
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError

class User(models.Model):
    _name = 'user'
    _order = 'id'
    _description = 'User'
    _rec_name = 'account_number'

    name = fields.Char(string="Name")
    login = fields.Char(string="Email")
    user_id = fields.Many2one('res.users', 'User')
    account_number = fields.Char(string="Account Number", compute="_compute_account_number", store=True )

    @api.depends('user_id')
    def _compute_account_number(self):
        acc_prefix = ""
        for user in self:
            current_id = user.id
            if len(str(current_id)) < 6:
                diff = 6 - len(str(current_id))
                zeroes = "0" * diff
                acc_prefix += zeroes + str(current_id)
            else:
                acc_prefix = str(current_id)  
            user.account_number = "ID-" + acc_prefix

    # def name_get(self):
    #     res=[]
    #     for rec in self:
    #         name = f'{rec.account_number} - {rec.name}'
    #         res.append((rec.id,name))
    #     return res
            
    @api.model
    def search_read(self, domain=None, fields=None, offset=0, limit=None, order=None):
        current_user = self.env.user
        if current_user.has_group('base.group_erp_manager'):
            return super(User, self).search_read(domain=domain, fields=fields, offset=offset, limit=limit, order=order)
        else:
            current_user_name = current_user.name
            if current_user_name:
                domain = domain or []
                domain.append(('name', '=', current_user_name))
            return super(User, self).search_read(domain=domain, fields=fields, offset=offset, limit=limit, order=order)
