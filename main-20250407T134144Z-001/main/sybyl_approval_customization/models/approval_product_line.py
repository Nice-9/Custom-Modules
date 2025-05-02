from odoo import api, fields, models, _

class ApprovalProductLine(models.Model):
    _inherit = 'approval.product.line'

    sale_order_line_id = fields.Many2one('sale.order.line')
