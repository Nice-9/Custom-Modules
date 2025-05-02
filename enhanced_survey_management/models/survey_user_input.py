# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Mohammed Savad, Ahammed Harshad (odoo@cybrosys.com)
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
import json
from odoo import models, fields, api
import re


class SurveyUserInput(models.Model):
    """Inherited user input to make acceptable for custom question"""
    _inherit = "survey.user_input"

    date_of_birth = fields.Date()
    postal_address = fields.Char()
    city = fields.Char()
    country = fields.Char()
    occupation = fields.Char()
    mobile_no = fields.Char()
    national_id = fields.Char()

    # def _save_lines(self, question, answer, comment=None):
    def _save_lines(self, question, answer, comment=None, overwrite_existing=True):
        """Function to save custom answers"""
        old_answers = self.env['survey.user_input.line'].search([
            ('user_input_id', '=', self.id),
            ('question_id', '=', question.id), ])
        if question.question_type in ['password', 'range', 'time', 'url',
                                      'email', 'range', 'many2many',
                                      'upload_file', 'many2one', 'week', 'color',
                                      'month', 'address', 'name', 'selection',
                                      'upload_file', 'qr', 'barcode', 'signature','file']:
            res = self._save_user_answers(question, old_answers, answer)
        elif question.matrix_subtype == 'custom':
            res = self._save_user_answers(question, old_answers, answer)
        else:
            if question.question_type in ('char_box','date') and (question.answer_validation in ('save_as_dob','save_as_postal_address','save_as_city','save_as_country','save_as_occupation','save_as_mobile','save_as_national_id')):
                res = super()._save_lines(question, answer, comment, overwrite_existing=True)
            else:
                res = super()._save_lines(question, answer, comment, overwrite_existing)

        return res


    @api.model
    def save_line_file(self, question, old_answers, answer, comment):
        vals = self._get_line_answer_values(question, answer, question.question_type)
        attachment_ids = []
        if answer:
            attachment_ids = answer.split(',')
            attachment_ids = [(4, int(a)) for a in attachment_ids]

            vals.update({'attachment_ids': attachment_ids})
        if old_answers:
            old_answers.write(vals)
        else:
            old_answers.create(vals)
        return True

    def _save_line_simple_answer(self, question, old_answers, answer):
        res = super()._save_line_simple_answer(question, old_answers, answer)
        partner_id = self.env.user.partner_id
        if res.question_id.question_type in ['char_box','date'] and partner_id:
            if res.question_id.answer_validation == 'save_as_dob':
                partner_id.write({'date_of_birth':answer})
            elif res.question_id.answer_validation == 'save_as_occupation':
                partner_id.write({'occupation':answer})
            elif res.question_id.answer_validation == 'save_as_email':
                partner_id.write({'email':answer})
            elif res.question_id.answer_validation == 'save_as_national_id':
                partner_id.write({'national_id':answer})
            elif res.question_id.answer_validation == 'save_as_mobile':
                partner_id.write({'mobile':answer})
            elif res.question_id.answer_validation == 'save_as_city':
                partner_id.write({'city':answer})
            elif res.question_id.answer_validation == 'save_as_country':
                country_id = self.env['res.country'].sudo().search([('name','=',answer)])
                if country_id:
                    partner_id.write({'country_id':country_id.id})
        return res


    def _save_user_answers(self, question, user_input_line, answer):
        """Function to save custom answers"""
        vals = (self._get_user_answers(
            question, answer, question.question_type))
        if user_input_line:
            user_input_line.write(vals)
        else:
            user_input_line = self.env['survey.user_input.line'].create(vals)
        return user_input_line

    def _get_user_answers(self, question, answer, answer_type):
        """Function to save custom answers"""
        vals = {'user_input_id': self.id, 'question_id': question.id,
                'skipped': False, 'answer_type': answer_type,
                }
        if not answer or (isinstance(answer, str) and not answer.strip()):
            vals.update(answer_type=None, skipped=True)
            return vals
        if question.question_type == 'time':
            vals['value_time'] = float(answer.replace(":", "."))
        elif question.question_type == 'url':
            vals['value_url'] = answer
        elif question.question_type == 'password':
            vals['value_password'] = answer
        elif question.question_type == 'email':
            vals['value_email'] = answer
        elif question.question_type == 'range':
            vals['value_range'] = answer
        elif question.question_type == 'many2one':
            vals['value_many2one'] = answer[0]
            vals['value_many2one_option'] = answer[1]
        elif question.question_type == 'many2many':
            vals['value_many2many'] = answer
        elif question.question_type == 'week':
            vals['value_week'] = answer
        elif question.question_type == 'color':
            vals['value_color'] = answer
        elif question.question_type == 'month':
            vals['value_month'] = answer
        elif question.question_type == 'matrix' \
                and question.matrix_subtype == 'custom':
            vals['value_matrix'] = json.dumps(answer)
        elif question.question_type == 'address':
            vals['value_address'] = json.dumps(answer)
        elif question.question_type == 'qr':
            vals['value_qr'] = json.dumps(answer)
        elif question.question_type == 'barcode':
            vals['value_barcode'] = json.dumps(answer)
        elif question.question_type == 'name':
            vals['value_name'] = json.dumps(answer)
        elif question.question_type == 'selection':
            vals['value_selection'] = answer
        elif question.question_type == 'file':
            attachment_ids = []
            vals['value_file'] = answer
            if answer:
                attachment_ids = answer.split(',')
                attachment_ids = [(4, int(a)) for a in attachment_ids]

                vals.update({'attachment_ids': attachment_ids})
        elif question.question_type == 'upload_file':
            # attachment = self.env['ir.attachment'].create({
            #     'name': str(answer[1]), 'datas': answer[0], 'type': 'binary'
            # })
            # vals['value_file'] = int(attachment.id if attachment else False)
            # vals['filename'] = attachment.name if attachment else False
            file_data = answer[0]
            file_name = answer[1]
            attachment_ids = []
            for file in range(len(answer[1])):
                attachment = self.env['ir.attachment'].create({
                    'name': file_name[file],
                    'type': 'binary',
                    'datas': file_data[file],
                })
                attachment_ids.append(attachment.id)
            vals['value_file_data_ids'] = attachment_ids
        return vals

    def _save_line_matrix(self, question, old_answers, answers, comment):
        """Function to save custom matrix"""
        if question.matrix_subtype == 'custom':
            self._save_line(question, answers)
        else:
            vals_list = []
            if not answers and question.matrix_row_ids:
                # add a False answer to force saving a skipped line
                # this will make this question correctly considered as
                # skipped in statistics
                answers = {question.matrix_row_ids[0].id: [False]}
            if answers:
                for row_key, row_answer in answers.items():
                    for answer in row_answer:
                        vals = self._get_line_answer_values(question, answer,
                                                            'suggestion')
                        vals['matrix_row_id'] = int(row_key)
                        vals_list.append(vals.copy())
            if comment:
                vals_list.append(
                    self._get_line_comment_values(question, comment))
            old_answers.sudo().unlink()
            return self.env['survey.user_input.line'].create(vals_list)

    def _save_line_selection_answer(self, question, answer):
        """Function to save selection type answers"""
        vals = self._get_line_answer_values(question, answer,
                                            question.question_type)
        return self.env['survey.user_input.line'].create(vals)
