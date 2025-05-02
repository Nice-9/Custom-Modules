# -*- coding: utf-8 -*-
################################################################################
#
#    Kolpolok Ltd. (https://www.kolpolok.com)
#    Author: Kaushik Ahmed Apu, Zarin Tasnim, Aqil Mahmud(<https://www.kolpolok.com>)
#
################################################################################
from odoo import api, fields, models, _


class FileInformation(models.Model):
    _name = 'file.information'
    _order = "name"
    _description = "File Information"
    
    # Fields definition for the File Information model
    name = fields.Char(string="File Name")
    file_info= fields.Char(string="File Information")