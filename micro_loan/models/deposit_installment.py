# -*- coding: utf-8 -*-
################################################################################
#
#    Kolpolok Ltd. (https://www.kolpolok.com)
#    Author: Kaushik Ahmed Apu, Zarin Tasnim, Aqil Mahmud(<https://www.kolpolok.com>)
#
################################################################################
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from datetime import datetime, timedelta

class DepositInstallment(models.Model):
    _name = 'deposit.installment'
    _order = 'id'
    _description = 'Deposit Installment'
    _rec_name  = 'account_number_id'
    
    name = fields.Char(string="Name")
    account_number_id = fields.Many2one('user', string="Account Number")
    amount = fields.Float(string="Amount")
    installment = fields.Integer(string="Installment")
    loan_type_id = fields.Many2one('loan.type', string="Deposit Type")
    date = fields.Date(string="Date", default=fields.Date.today())
    deposit_line_ids = fields.One2many('deposit.line', 'deposit_id', string="Deposit")


    #Nominee's information
    nominee_name = fields.Char(string='Name of Nominee')
    gender = fields.Selection ([ 
        ('male', 'Male'),
        ('female', 'Female'),
        ('other', 'Others'),
    ])
    nominee_relation = fields.Char(string='Relationship with Applicant')
    nominee_nationality = fields.Char(string='Nationality')
    nominee_birth = fields.Date(string='Date Of Birth')
    nominee_nid = fields.Integer(string='NID NO')
    nominee_address = fields.Text(string='Address')
    nominee_email = fields.Char(string='Email')
    nominee_contact = fields.Char(string='Contact No')
    nominee_sign = fields.Binary(string='Signature')
    nominee_photo = fields.Binary(string='Photo')

    @api.onchange('account_number_id')
    def onchange_account_number_id(self):
        for rec in self:
            rec.name = self.account_number_id.name

    
    @api.onchange('amount', 'installment', 'loan_type_id')
    def onchange_installment(self):
        ''' This method is used to compute the loan disbursement amortization line '''
        if self.installment:
            self.deposit_line_ids = [(5, 0, 0)]
            deposit_line_ids = []
            remaining_capital = 0.0
            collection_start_date_increment = self.loan_type_id.num_of_days
            for i in range(1, self.installment+1): 
                deposit_line_ids.append((0, 0, {
                    'serial_number': i,
                    'capital_payment': self.amount/self.installment,
                    'collection_date': self.date + timedelta(days=collection_start_date_increment)*i,
                    }))
            self.deposit_line_ids = deposit_line_ids
            deposit_line_ids_2 = self.deposit_line_ids
            for rec in deposit_line_ids_2:
                rec.due_date_amount = rec.capital_payment

    
    @api.model
    def search_read(self, domain=None, fields=None, offset=0, limit=None, order=None):
        current_user = self.env.user
        if current_user.has_group('base.group_erp_manager'):  
            return super(DepositInstallment, self).search_read(domain=domain, fields=fields, offset=offset, limit=limit, order=order)
        else:
            current_user_name = current_user.name
            if current_user_name:
                domain = domain or []
                domain.append(('name', '=', current_user_name))
            return super(DepositInstallment, self).search_read(domain=domain, fields=fields, offset=offset, limit=limit, order=order)



class DepositLine(models.Model):
    _name = "deposit.line"
    _order = "id"
    _description = "Deposit Installment Line"

    # Fields for Deposit Installment Line
    name = fields.Integer(string='Installment No')
    serial_number = fields.Integer(string='Installment No')
    capital_payment = fields.Float(string='Capital Payment')
    due_date_amount = fields.Float(string='Due Date Amount')
    collection_status = fields.Boolean(string='Collection Status')
    collection_amount = fields.Float(string='Collection Amount')
    collection_date = fields.Date(string='Collection Date')
    deposit_id = fields.Many2one('deposit.installment', string="Deposit Line name")