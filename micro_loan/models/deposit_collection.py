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

class DepositCollection(models.Model):
    _name = 'deposit.collection'
    _order = 'id'
    _description = 'Deposit Collection'
    _rec_name  = 'installment_id'
    
    
    name = fields.Char(string="Name")
    installment_id = fields.Many2one('deposit.installment', string="Deposit Account Number")
    deposit_amount = fields.Integer(string="Amount")
    deposit_installment = fields.Integer(string="Installment")
    date = fields.Date(string="Date")
    deposit_interest_rate = fields.Integer(string="Interest Rate")
    loan_type = fields.Char(string="Loan Type")
    is_clear = fields.Boolean(string="Is Clear")
    deposit_collection_line_ids = fields.One2many('deposit.collection.line', 'collection_id', string="Collection")

    @api.onchange('installment_id')
    def onchange_installment_id(self):
        for rec in self:
            rec.name = self.installment_id.name
            rec.deposit_amount = self.installment_id.amount
            rec.deposit_installment = self.installment_id.installment
            rec.date = self.installment_id.date
            self.loan_type = self.installment_id.loan_type_id.name

    @api.onchange('deposit_amount','deposit_interest_rate')
    def onchange_deposit_installment(self):
        ''' This method is used to compute the loan disbursement amortization line '''
        if self.deposit_installment:
            self.deposit_collection_line_ids = [(5, 0, 0)]
            deposit_collection_line_ids = []
            remaining_capital = 0.0
            collection_start_date_increment = self.installment_id.loan_type_id.num_of_days
            for i in range(1, self.deposit_installment+1): 
                deposit_collection_line_ids.append((0, 0, {
                    'serial_number': i,
                    'capital_repayment': self.deposit_amount/self.deposit_installment,
                    'interest_payment': (self.deposit_amount/self.deposit_installment)*(self.deposit_interest_rate/100),
                    'collection_date': self.date + timedelta(days=collection_start_date_increment)*i,
                    }))
            self.deposit_collection_line_ids = deposit_collection_line_ids
            deposit_collection_line_ids_2 = self.deposit_collection_line_ids
            for rec in deposit_collection_line_ids_2:
                rec.due_date_amount = rec.capital_repayment


class CollectionLine(models.Model):
    _name = "deposit.collection.line"
    _order = "id"
    _description = "Deposit Collection Line"

    # Fields for Deposit Collection Line
    name = fields.Integer(string='Installment No')
    serial_number = fields.Integer(string='Installment No')
    capital_repayment = fields.Float(string='Capital Payment')
    interest_payment = fields.Float(string='Interest Payment')
    due_date_amount = fields.Float(string='Due Date Amount')
    collection_status = fields.Boolean(string='Collection Status')
    collection_amount = fields.Float(string='Collection Amount')
    collection_date = fields.Date(string='Collection Date')
    collection_id = fields.Many2one('deposit.collection', string="Deposit Collection Line")


    @api.onchange('collection_status')
    def onchange_collection_status(self):
        for rec in self:
            if rec.collection_status:
                temp = rec.collection_amount
                rec.collection_amount = rec.due_date_amount
                rec.due_date_amount = temp
            else:
                rec.due_date_amount = rec.collection_amount
                rec.collection_amount = 0.0
        
        self.update_disbursement_line()

    def update_disbursement_line(self):
        for rec in self: 
            if rec.collection_id and rec.collection_id.installment_id:
                disbursement_line = rec.collection_id.installment_id.deposit_line_ids.filtered(lambda x: x.serial_number == rec.serial_number)
                disbursement_line.write({
                    'collection_status': rec.collection_status,
                    'collection_amount': rec.collection_amount,
                    'due_date_amount': rec.due_date_amount,
                })