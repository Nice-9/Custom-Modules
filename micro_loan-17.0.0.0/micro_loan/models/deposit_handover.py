# -*- coding: utf-8 -*-
################################################################################
#
#    Kolpolok Ltd. (https://www.kolpolok.com)
#    Author: Kaushik Ahmed Apu, Zarin Tasnim, Aqil Mahmud(<https://www.kolpolok.com>)
#
################################################################################
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError

class DepositHandover(models.Model):
    _name = 'deposit.handover'
    _order = 'id'
    _description = 'Deposit Handover'

    name = fields.Char(string="Name")
    name_2 = fields.Char(related="name")
    deposit_handover_id = fields.Many2one('deposit.collection', string="Deposit Handover Number")
    handover_amount = fields.Integer(string="Amount")
    handover_amount_2 = fields.Integer(related="handover_amount")
    interest_rate = fields.Integer(string="Interest Rate")
    interest_rate_2 = fields.Integer(related="interest_rate")
    interest_payment = fields.Float(string="Interest Payment")
    interest_payment_2 = fields.Float(related="interest_payment")
    net_amount = fields.Float(string="Net Amount")
    net_amount_2 = fields.Float(related="net_amount")
    installment = fields.Integer(string="Installment")
    installment_2 = fields.Integer(related="installment")

    @api.onchange('deposit_handover_id','handover_amount','interest_rate')
    def onchange_deposit_handover_id(self):
        for rec in self:
            rec.name = self.deposit_handover_id.name
            rec.handover_amount = self.deposit_handover_id.deposit_amount
            rec.interest_rate = self.deposit_handover_id.deposit_interest_rate
            rec.installment = self.deposit_handover_id.deposit_installment
            self.interest_payment = (rec.handover_amount)*(rec.interest_rate/100)
            self.net_amount = (rec.interest_payment + rec.handover_amount)
            
    @api.model
    def search_read(self, domain=None, fields=None, offset=0, limit=None, order=None):
        current_user = self.env.user
        if current_user.has_group('base.group_erp_manager'):  
            return super(DepositHandover, self).search_read(domain=domain, fields=fields, offset=offset, limit=limit, order=order)
        else:
            current_user_name = current_user.name
            if current_user_name:
                domain = domain or []
                domain.append(('name', '=', current_user_name))
            return super(DepositHandover, self).search_read(domain=domain, fields=fields, offset=offset, limit=limit, order=order)


  