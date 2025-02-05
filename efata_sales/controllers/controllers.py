# -*- coding: utf-8 -*-
# from odoo import http


# class EfataSales(http.Controller):
#     @http.route('/efata_sales/efata_sales', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/efata_sales/efata_sales/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('efata_sales.listing', {
#             'root': '/efata_sales/efata_sales',
#             'objects': http.request.env['efata_sales.efata_sales'].search([]),
#         })

#     @http.route('/efata_sales/efata_sales/objects/<model("efata_sales.efata_sales"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('efata_sales.object', {
#             'object': obj
#         })

