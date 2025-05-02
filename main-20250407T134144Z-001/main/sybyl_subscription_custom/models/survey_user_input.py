from odoo import fields, models, _
from datetime import timedelta


class SurveyUserInput(models.Model):
    _inherit = "survey.user_input"

    def _prepare_product_vals(self):
        product_qty_input_lines = self.user_input_line_ids.filtered(
            lambda x: not x.skipped and x.value_quantity
        )
        vals_list = []
        for rec in product_qty_input_lines:
            if rec.value_quantity and rec.value_product_id:
                vals_list.append(
                    {
                        "product_id": rec.suggested_answer_id.product_id.id,
                        "quantity": rec.value_quantity,
                        # "unit_price": rec.value_product_id.id,
                        "subscription_type_id": rec.value_subscription_type_id.id,
                    }
                )
        if vals_list:
            return [(0, 0, record) for record in vals_list]
        else:
            return vals_list
