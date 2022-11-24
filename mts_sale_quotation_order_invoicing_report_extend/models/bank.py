# -*- coding: utf-8 -*-

from odoo import models, fields, api

class BankInformation(models.Model):
    _inherit = 'res.bank'

    branch_name = fields.Char('Branch Name')
    bank_code = fields.Char('Bank Code')
    branch_code = fields.Char('Branch Code')
    transfer_code = fields.Char('Transfer Code')

