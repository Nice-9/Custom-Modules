# -*- coding: utf-8 -*-

from odoo.exceptions import ValidationError

from odoo import api, models, _


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    @api.constrains("tax_ids")
    @api.onchange("tax_ids")
    def _onchange_restrict_tax_ids(self):
        for line in self:
            if len(line.tax_ids) > 1:
                raise ValidationError(
                    _("Line Item not allowed to have more than one tax.")
                )
