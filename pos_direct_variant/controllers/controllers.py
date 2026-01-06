# -*- coding: utf-8 -*-
# from odoo import http


# class PosDirectVariant(http.Controller):
#     @http.route('/pos_direct_variant/pos_direct_variant', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/pos_direct_variant/pos_direct_variant/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('pos_direct_variant.listing', {
#             'root': '/pos_direct_variant/pos_direct_variant',
#             'objects': http.request.env['pos_direct_variant.pos_direct_variant'].search([]),
#         })

#     @http.route('/pos_direct_variant/pos_direct_variant/objects/<model("pos_direct_variant.pos_direct_variant"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('pos_direct_variant.object', {
#             'object': obj
#         })

