# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Mohammed Savad, Ahammed Harshad  (odoo@cybrosys.com)
#
#    This program is under the terms of the Odoo Proprietary License v1.0(OPL-1)
#    It is forbidden to publish, distribute, sublicense, or sell copies of the
#    Software or modified copies of the Software.
#
#    THE SOFTWARE IS PROVIDED “AS IS”, WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#    IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#    FITNESS FOR A PARTICULAR PURPOSE AND NON INFRINGEMENT. IN NO EVENT SHALL
#    THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM,DAMAGES OR OTHER
#    LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE,ARISING
#    FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
#    DEALINGS IN THE SOFTWARE.
#
###############################################################################
from odoo import fields, models, api
from odoo.http import request

class Survey(models.Model):
    """Inherited model to change survey visibility"""
    _inherit = 'survey.survey'

    access_mode = fields.Selection(selection_add=[
        ('website', 'website')], ondelete={'website': 'cascade'})
    visibility = fields.Boolean(string='Portal Visibility',
                                help="""Portal visibility of this survey""")

    def action_answer_report_download(self):
        """Function to generate report values"""
        return {
            'type': 'ir.actions.act_url',
            'url': f'/xlsx_report/{self.id}'
        }

    def _create_answer(self, user=False, partner=False, email=False, test_entry=False, check_attempts=True, **additional_vals):
        result = super(Survey , self)._create_answer(user=user, partner=partner, email=email, test_entry=test_entry, check_attempts=check_attempts, **additional_vals)
        answer_vals = {}
        if request.env.user and request.env.user.partner_id:
            address = ''
            answer_vals['date_of_birth'] = user.partner_id.date_of_birth
            answer_vals['national_id'] = user.partner_id.national_id
            if user.partner_id.street:
                address += user.partner_id.street + ','
            if user.partner_id.street2:
                address += user.partner_id.street2 + ','
            if user.partner_id.city:
                address += user.partner_id.city + ','
            if user.partner_id.state_id:
                address += user.partner_id.state_id.name + ','
            if user.partner_id.zip:
                address += user.partner_id.zip + ','
            if user.partner_id.country_id:
                address += user.partner_id.country_id.name + ','
            answer_vals['postal_address'] = address
            answer_vals['city'] = user.partner_id.city
            answer_vals['country'] = user.partner_id.country_id.name
            answer_vals['occupation'] = user.partner_id.occupation
            answer_vals['mobile_no'] = user.partner_id.mobile
        for rec in result:
            if not rec.email:
                answer_vals['email'] = user.partner_id.email
            if not rec.nickname:
                answer_vals['nickname'] = user.partner_id.name
            rec.sudo().write(answer_vals)
        for question in self.mapped('question_ids').filtered(
                lambda q: q.question_type in ('char_box','date') and (q.answer_validation in ('save_as_dob','save_as_postal_address','save_as_city','save_as_country','save_as_occupation','save_as_mobile','save_as_national_id'))):
            for user_input in result:
                if question.answer_validation == 'save_as_dob' and user_input.date_of_birth:
                    user_input._save_lines(question, user_input.date_of_birth,None,True)
                if question.answer_validation == 'save_as_postal_address' and user_input.postal_address:
                    user_input._save_lines(question, user_input.postal_address,None,True)
                if question.answer_validation == 'save_as_city' and user_input.city:
                    user_input._save_lines(question, user_input.city,None,True)
                if question.answer_validation == 'save_as_country' and user_input.country:
                    user_input._save_lines(question, user_input.country,None,True)
                if question.answer_validation == 'save_as_occupation' and user_input.occupation:
                    user_input._save_lines(question, user_input.occupation,None,True)
                if question.answer_validation == 'save_as_mobile' and user_input.mobile_no:
                    user_input._save_lines(question, user_input.mobile_no,None,True)
                if question.answer_validation == 'save_as_national_id' and user_input.national_id:
                    user_input._save_lines(question, user_input.national_id,None,True)
        return result

    @api.model
    def prepare_result(self, question, current_filters=None):
        current_filters = current_filters if current_filters else []
        result_summary = {}
        input_lines = question.user_input_line_ids.filtered(lambda line: not line.user_input_id.test_entry)

        # Calculate and return statistics for attachment
        if question.question_type == 'file':
            result_summary = []
            for input_line in input_lines:
                if not(current_filters) or input_line.user_input_id.id in current_filters:
                    result_summary.append(input_line)
            return result_summary
        else:
            return super(Survey, self).prepare_result(question, current_filters=current_filters)
