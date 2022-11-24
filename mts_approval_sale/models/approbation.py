# -*- coding:utf-8 -*-

from odoo import models, fields


class Approbation(models.Model):
    _name = "approval.flow.approbation"
    _inherit = "approval.flow.approbation"

    sale = fields.Many2one('sale.order', string='sales')
    quotation = fields.Many2one('sale.order', string='Quotation')
    sale_order = fields.Many2one('sale.order', string='Sale Order')