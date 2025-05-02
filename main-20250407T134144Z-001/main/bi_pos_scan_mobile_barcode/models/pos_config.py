# -*- coding: utf-8 -*-
from odoo import fields, models


class PosConfigInherit(models.Model):
    _inherit = 'pos.config'

    scan_mobile_type = fields.Selection([
        ('int_ref', 'Internal Reference'),
        ('barcode', 'Barcode'),
        ('qr_code', 'QR code'),
        ('all', 'All')
    ], string='POS Product Scan Options In Mobile', readonly=False, default='barcode')

    continue_scan = fields.Boolean(string='Continue scan product', default=False)
    product_success = fields.Boolean(string='Product success Notification', default=False)
    product_faild = fields.Boolean(string='Product Faild Notification', default=False)
    product_success_sound = fields.Boolean(string='Product success play Sound', default=False)
    product_faild_sound = fields.Boolean(string='Product faild play sound', default=False)
    customer_scan = fields.Boolean(string='Continue scan Customer', default=True)

    def get_limited_partners_loading(self):
        self.env.cr.execute("""
            WITH pm AS
            (
                     SELECT   partner_id,
                              Count(partner_id) order_count
                     FROM     pos_order
                     GROUP BY partner_id)
            SELECT    id
            FROM      res_partner AS partner
            LEFT JOIN pm
            ON        (
                                partner.id = pm.partner_id)
            WHERE (
                partner.company_id=%s OR partner.company_id IS NULL
            )
            ORDER BY  COALESCE(pm.order_count, 0) DESC;
        """, [self.company_id.id])
        result = self.env.cr.fetchall()
        return result


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    scan_mobile_type = fields.Selection(related='pos_config_id.scan_mobile_type', readonly=False)
    continue_scan = fields.Boolean(related='pos_config_id.continue_scan', readonly=False)
    product_success = fields.Boolean(related='pos_config_id.product_success', readonly=False)
    product_faild = fields.Boolean(related='pos_config_id.product_faild', readonly=False)
    product_success_sound = fields.Boolean(related='pos_config_id.product_success_sound', readonly=False)
    product_faild_sound = fields.Boolean(related='pos_config_id.product_faild_sound', readonly=False)
    customer_scan = fields.Boolean(related='pos_config_id.customer_scan', readonly=False)


class POSSession(models.Model):
    _inherit = 'pos.session'

    def _loader_params_product_product(self):
        res = super(POSSession, self)._loader_params_product_product()
        fields = res.get('search_params').get('fields')
        fields.extend(['qr_code'])
        res['search_params']['fields'] = fields
        return res

    def _loader_params_res_partner(self):
        res = super(POSSession, self)._loader_params_res_partner()
        fields = res.get('search_params').get('fields')
        fields.extend(['qr_sequence','child_ids','title','image_128','display_name','user_id','subscription_state','check_in_out_state','dog_ids','car_ids'])
        res['search_params']['fields'] = fields
        return res

    def _pos_ui_models_to_load(self):
        result = super()._pos_ui_models_to_load()
        if 'subscription.dog' not in result or 'subscription.vehicle' not in result:
            result.extend(['subscription.dog','subscription.vehicle','sale.order','sale.order.line'])
        return result

    def _loader_params_subscription_dog(self):
        return {
            'search_params': {
                'domain': [],
                'fields': ['name', 'image', 'breed_id','gender','check_in_out_state','color','next_vaccination_date'],
            },
        }

    def _loader_params_subscription_vehicle(self):
        return {
            'search_params': {
                'domain': [],
                'fields': ['name', 'image','check_in_out_state','color'],
            },
        }

    def _loader_params_sale_order_line(self):
        return {
            'search_params': {
                'fields': ['subscription_type_id','subscription_type_code','order_partner_id','order_id'],
            },
        }

    def _loader_params_sale_order(self):
        return {
            'search_params': {
                'domain': [('is_subscription', '=', True), ('subscription_state', 'in', ['3_progress', '6_churn', '4_paused'])],
                'fields': ['subscription_type_id','subscription_type_code','partner_id','name','next_invoice_date','subscription_state','date_order','state'],
            },
        }

    def _get_pos_ui_subscription_dog(self, params):
        return self.env['subscription.dog'].search_read(**params['search_params'])

    def _get_pos_ui_subscription_vehicle(self, params):
        return self.env['subscription.vehicle'].search_read(**params['search_params'])

    def _get_pos_ui_sale_order(self, params):
        return self.env['sale.order'].sudo().search_read(**params['search_params'])

    def _get_pos_ui_sale_order_line(self, params):
        return self.env['sale.order.line'].sudo().search_read(**params['search_params'])



