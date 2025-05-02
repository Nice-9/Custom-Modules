from odoo import fields, models, api, _
from datetime import datetime, date


class ResPartner(models.Model):
    _inherit = "res.partner"

    date_of_birth = fields.Date(string="Date of Birth")
    occupation = fields.Char(string="Occupation")
    national_id = fields.Char(string="National ID/Passport")
    registration_num = fields.Char(string="National ID/Passport")

    def is_valid_date(self, date_str, date_format):
        try:
            datetime.strptime(date_str, date_format)
            return True
        except ValueError:
            return False

    def write(self, vals):
        if "date_of_birth" in vals:
            date_format = "%m/%d/%Y"
            if (
                not isinstance(vals["date_of_birth"], date)
                and not isinstance(vals["date_of_birth"], bool)
                and not isinstance(vals["date_of_birth"], list)
            ):
                if self.is_valid_date(vals["date_of_birth"], date_format):
                    dob = datetime.strptime(vals["date_of_birth"], "%m/%d/%Y")
                    vals.update({"date_of_birth": dob.strftime("%Y-%m-%d")})
        res = super().write(vals)
        return res

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        if "type" in res:
            if res["type"] != "contact":
                res.update({"type": "contact"})
        return res
