# -*- coding: utf-8 -*-
################################################################################
#
#    Kolpolok Ltd. (https://www.kolpolok.com)
#    Author: Kaushik Ahmed Apu, Zarin Tasnim, Aqil Mahmud(<https://www.kolpolok.com>)
#
################################################################################
from odoo import api, fields, models, _


class LoanType(models.Model):
    _name = 'loan.type'
    _order = "id"
    _description = "Loan Type"
    
    # Fields definition for the Loan Type model
    name = fields.Char(string="Loan Type")
    num_of_days= fields.Integer(string="Number of Days")
   