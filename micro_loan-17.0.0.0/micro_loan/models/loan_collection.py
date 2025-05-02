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

class LoanCollection(models.Model):
    _name = 'loan.collection'
    _order = 'id'
    _description = 'Loan Collection'
 
    name = fields.Char(string="Name")
    loan_disbursement_id = fields.Many2one('loan.disbursement', string='Collection Account', required=True)
    collection_amount = fields.Float(string="Amount")
    interest_rate = fields.Integer(string="Interest Rate")
    installment = fields.Integer(string="Installment")
    date = fields.Date(string="Date")
    loan_type = fields.Char(string="Loan Type")
    collection_line_ids = fields.One2many('collection.line', 'collection_id', string="Collection")

    @api.onchange('loan_disbursement_id')
    def onchange_loan_application_id(self):
        if self.loan_disbursement_id:
            self.name = self.loan_disbursement_id.name
            self.collection_amount = self.loan_disbursement_id.disbursement_amount
            self.interest_rate = self.loan_disbursement_id.interest_rate
            self.installment = self.loan_disbursement_id.installment
            self.loan_type = self.loan_disbursement_id.loan_type
            self.date = self.loan_disbursement_id.date

    @api.onchange('collection_amount')
    def onchange_installment(self):
        ''' This method is used to compute the loan disbursement amortization line '''
        if self.installment:
            self.collection_line_ids = [(5, 0, 0)]
            collection_line_ids = []
            remaining_capital = 0.0
            collection_start_date_increment = self.loan_disbursement_id.loan_application_id.loan_type_id.num_of_days
            for i in range(1, self.installment+1): 
                collection_line_ids.append((0, 0, {
                    'serial_number': i,
                    'remaining_capital': self.collection_amount - (self.collection_amount/self.installment)*(i),
                    'capital_repayment': self.collection_amount/self.installment,
                    'interest_repayment': (self.collection_amount/self.installment)*(self.interest_rate/100),
                    'collection_date': self.date + timedelta(days=collection_start_date_increment)*i,
                    }))
            self.collection_line_ids = collection_line_ids
            collection_line_ids_2 = self.collection_line_ids
            for rec in collection_line_ids_2:
                rec.due_date_amount = rec.capital_repayment + rec.interest_repayment


class CollectionLine(models.Model):
    _name = "collection.line"
    _order = "id"
    _description = "Loan Collection Line"

    # Fields for Collection Line
    name = fields.Integer(string='Installment No')
    serial_number = fields.Integer(string='Installment No')
    remaining_capital = fields.Float(string='Remaining Capital')
    capital_repayment = fields.Float(string='Capital Repayment')
    interest_repayment = fields.Float(string='Interest Repayment')
    due_date_amount = fields.Float(string='Due Date Amount')
    collection_status = fields.Boolean(string='Collection Status')
    collection_amount = fields.Float(string='Collection Amount')
    collection_date = fields.Date(string='Collection Date')
    collection_id = fields.Many2one('loan.collection', string="Collection Line name")

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
            if rec.collection_id and rec.collection_id.loan_disbursement_id:
                disbursement_line = rec.collection_id.loan_disbursement_id.disbursement_line_ids.filtered(lambda x: x.serial_number == rec.serial_number)
                disbursement_line.write({
                    'collection_status': rec.collection_status,
                    'collection_amount': rec.collection_amount,
                    'due_date_amount': rec.due_date_amount,
                })


        