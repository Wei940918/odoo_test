# -*- coding: utf-8 -*-

from odoo import api, fields, models


class QuotationRefusedReason(models.TransientModel):
    _name = 'quotation.refused.reason'
    _description = 'Refused Reason'

    reason_quotation = fields.Text('Reason', required=True)


    @api.multi
    def action_reason_apply_quotation(self):
        approval = self.env['sale.order'].browse(self.env.context.get('active_ids'))
        return approval.action_refuse_quotation(reason=self.reason_quotation)
