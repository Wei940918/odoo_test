# -*- coding: utf-8 -*-

from odoo import api, fields, models


class OrderRefusedReason(models.TransientModel):
    _name = 'order.refused.reason'
    _description = 'Refused Reason'

    reason = fields.Text('Reason', required=True)

    @api.multi
    def action_reason_apply(self):
        approval = self.env['sale.order'].browse(self.env.context.get('active_ids'))
        return approval.action_refuse(reason=self.reason)

