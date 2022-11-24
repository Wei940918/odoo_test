# -*- coding: utf-8 -*-
from odoo import http

# class MtsSaleQuotationOrderInvoicingReportExtend(http.Controller):
#     @http.route('/mts_sale_quotation_order_invoicing_report_extend/mts_sale_quotation_order_invoicing_report_extend/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/mts_sale_quotation_order_invoicing_report_extend/mts_sale_quotation_order_invoicing_report_extend/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('mts_sale_quotation_order_invoicing_report_extend.listing', {
#             'root': '/mts_sale_quotation_order_invoicing_report_extend/mts_sale_quotation_order_invoicing_report_extend',
#             'objects': http.request.env['mts_sale_quotation_order_invoicing_report_extend.mts_sale_quotation_order_invoicing_report_extend'].search([]),
#         })

#     @http.route('/mts_sale_quotation_order_invoicing_report_extend/mts_sale_quotation_order_invoicing_report_extend/objects/<model("mts_sale_quotation_order_invoicing_report_extend.mts_sale_quotation_order_invoicing_report_extend"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('mts_sale_quotation_order_invoicing_report_extend.object', {
#             'object': obj
#         })