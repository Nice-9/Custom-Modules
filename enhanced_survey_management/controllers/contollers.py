from odoo.http import request, route

from odoo.addons.account.controllers.portal import CustomerPortal
from odoo import http
from odoo.addons.survey.controllers.main import Survey  # Import the class
from odoo.addons.bt_ajax_upload_file_common.controllers.main import AttachmentUpload  # Import the class
from odoo.http import request, content_disposition
from odoo.exceptions import UserError
from odoo.tools import ustr
import json, sys, base64, pytz

class CustomerPortalAdditionalFields(CustomerPortal):

    def _get_optional_fields(self):
        """Extend optional fields to add the identification type to avoid having the unknown field error"""
        optional_fields = super()._get_optional_fields()
        optional_fields += ["mobile","date_of_birth","occupation","national_id","registration_num"]
        return optional_fields

    @route(["/my/account"], type="http", auth="user", website=True)
    def account(self, redirect=None, **post):
        values = self._prepare_portal_layout_values()
        partner = request.env.user.partner_id
        values.update(
            {
                "error": {},
                "error_message": [],
            }
        )

        if post and request.httprequest.method == "POST":
            error, error_message = self.details_form_validate(post)
            values.update({"error": error, "error_message": error_message})
            values.update(post)
            if not error:
                values = {key: post[key] for key in self._get_mandatory_fields()}
                values.update(
                    {
                        key: post[key]
                        for key in self._get_optional_fields()
                        if key in post
                    }
                )
                for field in set(["country_id", "state_id"]) & set(values.keys()):
                    try:
                        values[field] = int(values[field])
                    except:
                        values[field] = False
                values.update({"zip": values.pop("zipcode", "")})
                self.on_account_update(values, partner)
                partner.sudo().write(values)
                if redirect:
                    return request.redirect(redirect)
                return request.redirect("/my/home")

        countries = request.env["res.country"].sudo().search([])
        states = request.env["res.country.state"].sudo().search([])

        values.update(
            {
                "partner": partner,
                "countries": countries,
                "states": states,
                "has_check_vat": hasattr(request.env["res.partner"], "check_vat"),
                "partner_can_edit_vat": partner.can_edit_vat(),
                "redirect": redirect,
                "page_name": "my_details",
            }
        )

        response = request.render("custom_portal_account_page.portal_my_details_inh", values)
        response.headers["X-Frame-Options"] = "SAMEORIGIN"
        response.headers["Content-Security-Policy"] = "frame-ancestors 'self'"
        return response

class SurveyAttachmentUpload(AttachmentUpload):

    def add_attachment(self, ufile, res_model, res_id, res_field=False):
        if res_model == 'survey.user_input.line':
            # res_id = False
            # res_model = False
            res_field = 'attachment_ids'
        return super(SurveyAttachmentUpload, self).add_attachment(ufile, res_model, res_id, res_field=res_field)

    @http.route()        # Return non empty answers in a JSON compatible format
    def uploaded_files(self, **kw):
        if kw.get('res_model', '') == 'survey.user_input.line':
            res_id = kw.get('res_id', '')
            attachments = []
            if res_id:
                res_id = res_id.split('_')
                answer_sudo = request.env['survey.user_input.line'].sudo().search([
                    ('user_input_id', '=', int(res_id[1])),
                    ('survey_id', '=', int(res_id[0])),
                    ('question_id', '=', int(res_id[2]))
                ])
                for attach in answer_sudo.attachment_ids:
                    attachments.append({'path': attach.id, 'name': attach.name, 'size': attach.file_size})
            return attachments
        else:
            return super(SurveyAttachmentUpload, self).uploaded_files(**kw)
