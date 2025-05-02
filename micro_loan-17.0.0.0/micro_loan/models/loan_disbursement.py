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

class LoanDisbursement(models.Model):
    _name = 'loan.disbursement'
    _order = 'id'
    _description = 'Loan Disbursement'
    _rec_name  = 'loan_application_id'
    

    # Fields definition for the Loan Disbursement model
    name = fields.Char(string="Name")
    loan_application_id = fields.Many2one('loan.loan', string='Disbursement Account', required=True)
    disbursement_amount = fields.Float(string="Amount")
    interest_rate = fields.Integer(string="Interest Rate")
    installment = fields.Integer(string="Installment")
    date = fields.Date(string="Date")
    loan_type = fields.Char(string="Loan Type")
    disbursement_line_ids = fields.One2many('disbursement.line', 'disbursement_id', string="Disbursement")

    @api.onchange('loan_application_id')
    def onchange_loan_application_id(self):
        if self.loan_application_id:
            self.name = self.loan_application_id.name
            self.disbursement_amount = self.loan_application_id.amount
            self.interest_rate = self.loan_application_id.interest_rate
            self.installment = self.loan_application_id.installment
            self.loan_type = self.loan_application_id.loan_type_id.name
            self.date = self.loan_application_id.date

    @api.onchange('disbursement_amount')
    def onchange_installment(self):
        ''' This method is used to compute the loan disbursement amortization line '''
        if self.installment:
            self.disbursement_line_ids = [(5, 0, 0)]
            disbursement_line_ids = []
            remaining_capital = 0.0
            collection_start_date_increment = self.loan_application_id.loan_type_id.num_of_days
            for i in range(1, self.installment+1): 
                disbursement_line_ids.append((0, 0, {
                    'serial_number': i,
                    'remaining_capital': self.disbursement_amount - (self.disbursement_amount/self.installment)*(i),
                    'capital_repayment': self.disbursement_amount/self.installment,
                    'interest_repayment': (self.disbursement_amount/self.installment)*(self.interest_rate/100),
                    'collection_date': self.date + timedelta(days=collection_start_date_increment)*i,
                    }))
            self.disbursement_line_ids = disbursement_line_ids
            disbursement_line_ids_2 = self.disbursement_line_ids
            for rec in disbursement_line_ids_2:
                rec.due_date_amount = rec.capital_repayment + rec.interest_repayment
    
    @api.model
    def search_read(self, domain=None, fields=None, offset=0, limit=None, order=None):
        current_user = self.env.user
        if current_user.has_group('base.group_erp_manager'):  
            return super(LoanDisbursement, self).search_read(domain=domain, fields=fields, offset=offset, limit=limit, order=order)
        else:
            current_user_name = current_user.name
            if current_user_name:
                domain = domain or []
                domain.append(('name', '=', current_user_name))
            return super(LoanDisbursement, self).search_read(domain=domain, fields=fields, offset=offset, limit=limit, order=order)



class DisbursementLine(models.Model):
    _name = "disbursement.line"
    _order = "id"
    _description = "Loan Disbursement Line"

    # Fields for Disbursement Line
    name = fields.Integer(string='Installment No')
    serial_number = fields.Integer(string='Installment No')
    remaining_capital = fields.Float(string='Remaining Capital')
    capital_repayment = fields.Float(string='Capital Repayment')
    interest_repayment = fields.Float(string='Interest Repayment')
    due_date_amount = fields.Float(string='Due Date Amount')
    collection_status = fields.Boolean(string='Collection Status')
    collection_amount = fields.Float(string='Collection Amount')
    collection_date = fields.Date(string='Collection Date')
    disbursement_id = fields.Many2one('loan.disbursement', string="Disbursement Line name")