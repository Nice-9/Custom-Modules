# -*- coding: utf-8 -*-
################################################################################
#
#    Kolpolok Ltd. (https://www.kolpolok.com)
#    Author: Kaushik Ahmed Apu, Zarin Tasnim, Aqil Mahmud(<https://www.kolpolok.com>)
#
################################################################################
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError

class Loan(models.Model):
    _name = 'loan.loan'
    _order = 'id'
    _description = 'Loan'
    _rec_name = 'account_number_id'
    # Fields definition for the Loan model
    name = fields.Char(string="Name")
    account_number_id = fields.Many2one('user', string="Account Number")
    amount = fields.Float(string="Amount")
    interest_rate = fields.Integer(string="Interest Rate")
    installment = fields.Integer(string="Installment")
    date = fields.Date(string="Date", default=fields.Date.today())
    loan_type_id = fields.Many2one('loan.type', string="Loan Type")
    state= fields.Selection([
        ('entry','Entry'),
        ('approved', 'Approved'),
        ('rejected', 'Reject'),
    ], string= 'Status' , default='entry' , readonly=True, copy=False)
    file_info_line_ids = fields.One2many('file.info', 'loan_info_id', string="Loan Information")
    col_security_line_id = fields.One2many('collateral.security', 'col_security_id', string="Collateral Security")
    
    #Guarantor's information
    guarantor_name = fields.Char(string='Guarantor Name')
    gender = fields.Selection ([ 
        ('male', 'Male'),
        ('female', 'Female'),
        ('other', 'Others'),
    ])
    guarantor_relation = fields.Char(string='Relationship with Applicant')
    guarantor_nationality = fields.Char(string='Guarantor Nationality')
    guarantor_country = fields.Char(string='Guarantor Country')
    guarantor_birth = fields.Date(string='Guarantor Date Of Birth')
    guarantor_nid = fields.Integer(string='Guarantor NID NO')
    guarantor_city = fields.Char(string='Guarantor City/District')
    guarantor_state = fields.Char(string='Guarantor State/Division')
    guarantor_address = fields.Char(string='Guarantor Address')
    guarantor_email = fields.Char(string='Guarantor Email')
    guarantor_contact = fields.Char(string='Guarantor Contact No')
    guarantor_sign = fields.Binary(string='Guarantor Signature')
    guarantor_photo = fields.Binary(string='Guarantor Photo')

    @api.onchange('account_number_id')
    def onchange_account_number_id(self):
        for rec in self:
            rec.name = self.account_number_id.name
    
    def approve_loan(self):
        self.state = 'approved'
    
    def reject_loan(self):
        self.state = 'rejected'

    @api.model
    def search_read(self, domain=None, fields=None, offset=0, limit=None, order=None):
        current_user = self.env.user
        if current_user.has_group('base.group_erp_manager'):  
            return super(Loan, self).search_read(domain=domain, fields=fields, offset=offset, limit=limit, order=order)
        else:
            current_user_name = current_user.name
            if current_user_name:
                domain = domain or []
                domain.append(('name', '=', current_user_name))
            return super(Loan, self).search_read(domain=domain, fields=fields, offset=offset, limit=limit, order=order)



class FileInfo(models.Model):
    _name = 'file.info'
    _order = "id"
    _description = "Loan File Information"
 # Fields for the Loan File Information model
    file_info_id = fields.Many2one('file.information', string="File")
    file_info = fields.Char(string="File Information")
    file_upload = fields.Binary(string = "File Upload")
    loan_info_id = fields.Many2one('loan.loan', string="Loan Application name") 
        
    @api.onchange('file_info_id')
    def onchange_file_info_id(self):
        for rec in self:
            rec.file_info = self.file_info_id.file_info

    #Constraint to check whether 'file_upload' is provided
    @api.constrains('file_upload')
    def check_file(self):
        for rec in self:
            if not rec.file_upload:
                raise ValidationError(_('Please upload your file for %s') % rec.file_info) 


# Defining a new Odoo model for Collateral Security
class CollateralSecurity(models.Model):
    _name = "collateral.security"
    _order = "name"
    _description = "Collateral Security"

 # Fields for the Collateral Security model
    name = fields.Text(string="Security Description", required=True)
    account = fields.Char(string='Security Account')
    amount = fields.Char(string='Security Amount')
    col_security_id = fields.Many2one('loan.loan', string="Loan App")