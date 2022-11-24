# -*- coding: utf-8 -*-

from odoo import models, fields, api

class BankInformation(models.Model):
    _inherit = 'res.bank'

    # beneficiary = fields.Char('Beneficiary', default='MTS GLOBAL PTE.LTD.')
    # account_No = fields.Char('Account No')
    # swift_code = fields.Char('Swift Code')

# billing_contact = fields.Many2one('hr.employee')