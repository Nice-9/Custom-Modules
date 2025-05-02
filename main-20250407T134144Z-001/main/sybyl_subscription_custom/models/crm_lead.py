# Copyright 2023 Tecnativa - David Vidal
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.exceptions import ValidationError

from odoo import fields, models, api, _


class CrmLead(models.Model):
    _inherit = "crm.lead"

    
    def action_new_quotation_karura(self):
        new_quotation_context = self.action_new_quotation().get("context")
        filtered_dict = {
            key[len("default_") :]: value
            for key, value in new_quotation_context.items()
            if key.startswith("default_")
        }
        lines = []
        for survey_product_line_id in self.survey_product_line_ids:
            lines.append(
                (
                    0,
                    0,
                    {
                        "product_id": survey_product_line_id.product_id.id,
                        "product_template_id": survey_product_line_id.product_id.product_tmpl_id.id,
                        "name": survey_product_line_id.product_id.display_name,
                        "product_uom_qty": survey_product_line_id.quantity,
                        "product_uom": survey_product_line_id.product_id.uom_id.id,
                        "price_unit": survey_product_line_id.product_id.lst_price,
                        "subscription_type_id": survey_product_line_id.subscription_type_id.id,
                    },
                )
                )
        sale_order_ids = self.env["sale.order"].create(
            {
                "plan_id": self.env.ref(
                    "sale_subscription.subscription_plan_year"
                ).id,
                "order_line": lines,
                # "is_from_lead": True,
                **filtered_dict,
            }
        )
        return self.action_view_sale_quotation()
