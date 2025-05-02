# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.exceptions import UserError


class ApprovalRequest(models.Model):
    _inherit = 'approval.request'

    sale_order_count = fields.Integer(compute='_compute_sale_order_count')

    @api.depends('product_line_ids.sale_order_line_id')
    def _compute_sale_order_count(self):
        for request in self:
            if request.product_line_ids:
                sales = request.product_line_ids.sale_order_line_id.order_id
                request.sale_order_count = len(sales)
            else:
                request.sale_order_count = 0

    def action_approve(self, approver=None):
        if self.approval_type == 'sale' and any(not line.product_id for line in self.product_line_ids):
            raise UserError(_("You must select a product for each line of requested products."))
        return super().action_approve(approver)


    def action_confirm(self):
        for request in self:
            if request.approval_type == 'sale' and not request.product_line_ids:
                raise UserError(_("You cannot create an empty Quatation."))
        return super().action_confirm()

    def action_open_sale_orders(self):
        """ Return the list of purchase orders the approval request created or
        affected in quantity. """
        self.ensure_one()
        sale_ids = self.product_line_ids.sale_order_line_id.order_id.ids
        domain = [('id', 'in', sale_ids)]
        action = {
            'name': _('Sale Orders'),
            'view_type': 'tree',
            'view_mode': 'list,form',
            'res_model': 'sale.order',
            'type': 'ir.actions.act_window',
            'context': self.env.context,
            'domain': domain,
        }
        return action


    def action_create_sale_orders(self):
        """ Create and/or modifier Purchase Orders. """
        self.ensure_one()
        for line in self.product_line_ids:
            so_vals = {
            'partner_id' : self.partner_id.id
            }
            new_sale_order = self.env['sale.order'].create(so_vals)
            so_line_vals =  {
                'name': line.description,
                'product_qty': line.quantity,
                'product_id': line.product_id.id,
                'product_uom_qty': line.product_id.uom_po_id.id,
                'price_unit': line.product_id.lst_price,
                'order_id': new_sale_order.id,
            }
            new_so_line = self.env['sale.order.line'].create(so_line_vals)
            line.sale_order_line_id = new_so_line.id
            new_sale_order.order_line = [(4, new_so_line.id)]