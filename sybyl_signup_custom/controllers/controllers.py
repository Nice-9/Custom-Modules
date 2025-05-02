from odoo.http import request, route

from odoo.addons.auth_signup.controllers.main import AuthSignupHome

from odoo.addons.account.controllers.portal import CustomerPortal


class CustomerPortalmb(CustomerPortal):

    def _get_optional_fields(self):
        """Extend optional fields to add the identification type to avoid having the unknown field error"""
        optional_fields = super()._get_optional_fields()
        optional_fields += ["mobile"]
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
            if not partner.can_edit_vat():
                post["country_id"] = (
                    str(partner.country_id.id) if partner.country_id else ""
                )

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

        response = request.render("portal.portal_my_details", values)
        response.headers["X-Frame-Options"] = "SAMEORIGIN"
        response.headers["Content-Security-Policy"] = "frame-ancestors 'self'"
        return response


class AuthSignupHomeExt(AuthSignupHome):
    def _prepare_signup_values(self, qcontext):
        values = super(AuthSignupHomeExt, self)._prepare_signup_values(qcontext)
        result_list = []

        # Find the maximum number of logins
        login_numbers = [
            int(key.split("_")[1])
            for key in request.params.keys()
            if key.startswith("login_")
        ]
        if login_numbers:
            max_login_number = max(login_numbers)
        else:
            # Handle the case when there are no keys starting with "login_"
            max_login_number = 0 

        # Iterate through the range of login numbers
        for i in range(1, max_login_number + 1):
            login_key = f"login_{i}"
            name_key = f"name_{i}"

            # Check if both keys exist in the request.params
            if (
                login_key in request.params
                and request.params[login_key]
                and name_key in request.params
                and request.params[name_key]
            ):
                result_list.append(
                    {
                        "email": request.params[login_key],
                        "name": request.params[name_key],
                    }
                )
        child_ids = []
        for rec in result_list:
            partner_id = request.env["res.partner"].sudo().create(rec)
            child_ids.append(partner_id.id)
        if not request.params.get("token"):
            values.update(
                {
                    key: request.params[key]
                    for key in [
                        "mobile",
                        "street",
                        "city",
                        "zip",
                        "country_id",
                        "state_id",
                    ]
                }
            )
            if values.get("country_id"):
                values["country_id"] = int(values.get("country_id"))
            if values.get("state_id"):
                values["state_id"] = int(values.get("state_id"))
            values["phone"] = values.get("mobile")
            if result_list:
                values["child_ids_store"] = ",".join(
                    str(child_id) for child_id in child_ids
                )
        return values
