# -*- coding: utf-8 -*-
from odoo import http

# class MtsApprovalSale(http.Controller):
#     @http.route('/mts_approval_sale/mts_approval_sale/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/mts_approval_sale/mts_approval_sale/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('mts_approval_sale.listing', {
#             'root': '/mts_approval_sale/mts_approval_sale',
#             'objects': http.request.env['mts_approval_sale.mts_approval_sale'].search([]),
#         })

#     @http.route('/mts_approval_sale/mts_approval_sale/objects/<model("mts_approval_sale.mts_approval_sale"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('mts_approval_sale.object', {
#             'object': obj
#         })