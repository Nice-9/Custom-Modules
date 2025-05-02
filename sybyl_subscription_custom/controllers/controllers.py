# -*- coding: utf-8 -*-
# from odoo import http


# class SybylSubscription(http.Controller):
#     @http.route('/sybyl_subscription/sybyl_subscription', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/sybyl_subscription/sybyl_subscription/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('sybyl_subscription.listing', {
#             'root': '/sybyl_subscription/sybyl_subscription',
#             'objects': http.request.env['sybyl_subscription.sybyl_subscription'].search([]),
#         })

#     @http.route('/sybyl_subscription/sybyl_subscription/objects/<model("sybyl_subscription.sybyl_subscription"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('sybyl_subscription.object', {
#             'object': obj
#         })
