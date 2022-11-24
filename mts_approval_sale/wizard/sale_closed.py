# -*- coding: utf-8 -*-

from odoo import api, fields, models


class SaleLost(models.TransientModel):
    _name = 'sale.closed'
    _description = 'Get Closed Reason'

    sale_id = fields.Many2one('sale.order', 'Renewal Sale Order')
    closed_reason_id = fields.Many2one('sale.closed.reason', 'Closed Reason')

    @api.multi
    def action_closed_reason_apply(self):
        leads = self.env['sale.order'].browse(self.env.context.get('active_ids'))
        # leads.write({'lost_reason': self.lost_reason_id.id, 'sale_id': leads.id})

        leads.write({'closed_reason': self.closed_reason_id.id, 'sale_id': self.sale_id.id})
        return leads.action_set_lost()

