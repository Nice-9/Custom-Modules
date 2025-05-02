import logging
import re

from odoo.exceptions import ValidationError

from odoo import fields, models, api, _

_logger = logging.getLogger(__name__)


class ProductTemplate(models.Model):
    _inherit = "product.template"

    name = fields.Char(size=40)
    factor_type = fields.Selection(
        [("taxable", "Taxable"), ("exempted", "Exempted"), ("zero", "Zero Rated")],
        default="exempted",
        store=True,
        compute="_compute_factor_type",
    )
    hscode_index = fields.Char("HS Code Index", copy=False)

    @api.depends("taxes_id")
    def _compute_factor_type(self):
        for record in self:
            if len(record.taxes_id) == 1:
                record.factor_type = record.taxes_id.factor_type
            else:
                record.factor_type = False

    @api.onchange("taxes_id")
    @api.constrains("taxes_id")
    def _check_taxes_id(self):
        for record in self:
            if len(record.taxes_id) > 1:
                raise ValidationError(
                    _("Product not allowed to have more than one tax.")
                )

    @api.onchange("factor_type")
    def _onchange_factor_type(self):
        for record in self:
            if record.factor_type == "taxable":
                record.hscode_index = None

    # @api.constrains("name")
    # def _check_product_name(self):
    #     string_check = re.compile("[@_!#$%^&*()<>?/\|}{~:]")
    #     for record in self:
    #         if string_check.search(record.name):
    #             raise ValidationError("Special characters are not allowed")

    def cron_remove_special_character(self):
        string_check = re.compile("[@_!#$%^&*()<>?/\|}{~:]")
        _logger.info("Remove Special Character")
        for record in self.search([]):
            if string_check.search(record.name):
                _logger.info(record.name)
                clean_name = "".join(
                    e for e in record.name if (e.isalnum() or e.isspace())
                )
                _logger.info(clean_name)
                record.name = clean_name
