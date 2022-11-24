# -*- coding: utf-8 -*-

from odoo import models, fields, api
from datetime import datetime, timedelta
from odoo.addons import decimal_precision as dp
from odoo.tools.misc import formatLang
from functools import partial
from decimal import Decimal

class SaleOrderTemplate(models.Model):
    _inherit = "sale.order.template"
    note = fields.Html('note')


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    lost_reason = fields.Many2one(store=False)

    def _default_validity_date(self):
        if self.env['ir.config_parameter'].sudo().get_param('sale.use_quotation_validity_days'):
            days = self.env.user.company_id.quotation_validity_days
            if days > 0:
                return fields.Date.to_string(datetime.now() + timedelta(days))
        return False
    validity_date = fields.Date(string='Validity', readonly=True, copy=False,
                                states={'quotation approved': [('readonly', False)]},
                                help="Validity date of the quotation, after this date, the customer won't be able to validate the quotation online.",
                                default=_default_validity_date)
    po_start_date = fields.Date('PO Start Date')
    po_end_date = fields.Date('PO End Date')
    service_start_date = fields.Date('Service Start Date')
    service_end_date = fields.Date('Service End Date')
    #date_order = fields.Datetime(string='Order Date', required=True, states={}, default=fields.Datetime.now)
    date_order = fields.Datetime(string='Order Date', readonly=True, index=True,
                                 states={
                                         # 'draft': [('readonly', False)],
                                         # 'quotation approval': [('readonly', False)],
                                         # 'refuse quotation': [('readonly', False)],
                                         # 'quotation approved': [('readonly', False)],
                                         # 'order approval': [('readonly', False)],
                                         # 'refuse order': [('readonly', False)],
                                         'sale': [('readonly', False)],
                                         # 'done': [('readonly', False)],
                                         # 'cancel': [('readonly', False)],
                                         'sent': [('readonly', False)]
                                 },
                                 copy=False, default=fields.Datetime.now)
    # default = fields.Datetime.now

    note = fields.Html(default='')
    payment_milestone = fields.Integer(string="Payment Milestone(s)#")
    vendor_number = fields.Char(string='Vendor Number', required=True, default='N/A')
    po_number = fields.Char(string='PO No', required=True, readonly=True,states={'sent': [('readonly', False)]}, default='N/A')
    # date_order_copy = fields.Char(string='Order Date Copy', default=fields.datetime.strftime(datetime.utcnow() + timedelta(hours=8), '%Y-%m-%d'))
    # date_order_copy_one = fields.Char(string='Order Date Copy One', default=fields.datetime.strftime(datetime.utcnow() + timedelta(hours=8), '%Y%m%d'))
    date_order_copy_one = fields.Char(string='Order Date Copy One', default=lambda self: fields.Date.today().strftime('%Y%m%d'))

    # date_YY = fields.Char(string='YY', compute='_compute_YY')
    date_MM = fields.Char(string='MM', compute='_compute_MM')
    # add for sow 20220329 by kevin
    sow_num = fields.Integer(string="(P)SOW", default=0)

    has_sow = fields.Selection([('yes', 'Yes'), ('no', 'No')], required=False, string="(P)SOW")
    remarks_for_no_SOW = fields.Text('Remarks for no (P)SOW')

    # added by Kevin on 20221107
    is_timesheet_billing = fields.Selection([('yes', 'Yes'), ('no', 'No')], string="Timesheet Billing", default='no', index=True)

    def _compute_MM(self):
        self.ensure_one()
        if (self.date_order_copy_one)[4:6] == '01':
            self.date_MM = (self.date_order_copy_one)[6:8] + '-' + 'Jan'+ '-' + (self.date_order_copy_one)[0:4]
        elif (self.date_order_copy_one)[4:6] == '02':
            self.date_MM = (self.date_order_copy_one)[6:8] + '-' + 'Feb' + '-' + (self.date_order_copy_one)[0:4]
        elif (self.date_order_copy_one)[4:6] == '03':
            self.date_MM = (self.date_order_copy_one)[6:8] + '-' + 'Mar' + '-' + (self.date_order_copy_one)[0:4]
        elif (self.date_order_copy_one)[4:6] == '04':
            self.date_MM = (self.date_order_copy_one)[6:8]+ '-' + 'Apr' + '-' + (self.date_order_copy_one)[0:4]
        elif (self.date_order_copy_one)[4:6] == '05':
            self.date_MM = (self.date_order_copy_one)[6:8] + '-'+ 'May' + '-' + (self.date_order_copy_one)[0:4]
        elif (self.date_order_copy_one)[4:6] == '06':
            self.date_MM = (self.date_order_copy_one)[6:8] + '-'+ 'Jun' + '-' + (self.date_order_copy_one)[0:4]
        elif (self.date_order_copy_one)[4:6] == '07':
            self.date_MM = (self.date_order_copy_one)[6:8] + '-' + 'Jul' + '-' + (self.date_order_copy_one)[0:4]
        elif (self.date_order_copy_one)[4:6] == '08':
            self.date_MM = (self.date_order_copy_one)[6:8] + '-' + 'Aug' + '-' + (self.date_order_copy_one)[0:4]
        elif (self.date_order_copy_one)[4:6] == '09':
            self.date_MM = (self.date_order_copy_one)[6:8] + '-' + 'Sep' + '-' + (self.date_order_copy_one)[0:4]
        elif (self.date_order_copy_one)[4:6] == '10':
            self.date_MM = (self.date_order_copy_one)[6:8]+ '-'  + 'Oct' + '-' + (self.date_order_copy_one)[0:4]
        elif (self.date_order_copy_one)[4:6] == '11':
            self.date_MM = (self.date_order_copy_one)[6:8] + '-' + 'Nov'+ '-' + (self.date_order_copy_one)[0:4]
        elif (self.date_order_copy_one)[4:6] == '12':
            self.date_MM = (self.date_order_copy_one)[6:8] + '-' + 'Dec' + '-' + (self.date_order_copy_one)[0:4]
        else:
            self.date_MM = 'xxx'
    @api.multi
    def _prepare_invoice(self):
        """
        Prepare the dict of values to create the new invoice for a sales order. This method may be
        overridden to implement custom invoice generation (making sure to call super() to establish
        a clean extension chain).
        """
        self.ensure_one()
        company_id = self.company_id.id
        journal_id = (self.env['account.invoice'].with_context(company_id=company_id or self.env.user.company_id.id)
            .default_get(['journal_id'])['journal_id'])
        if not journal_id:
            raise UserError(_('Please define an accounting sales journal for this company.'))
        vinvoice = self.env['account.invoice'].new({'partner_id': self.partner_invoice_id.id, 'type': 'out_invoice'})
        # Get partner extra fields
        vinvoice._onchange_partner_id()
        invoice_vals = vinvoice._convert_to_write(vinvoice._cache)
        invoice_vals.update({
            'name': (self.client_order_ref or '')[:2000],
            'origin': self.name,
            'po_number': self.po_number,
            'vendor_number': self.vendor_number,
            'type': 'out_invoice',
            'account_id': self.partner_invoice_id.property_account_receivable_id.id,
            'partner_shipping_id': self.partner_shipping_id.id,
            'journal_id': journal_id,
            'currency_id': self.pricelist_id.currency_id.id,
            'comment': self.note,
            'payment_term_id': self.payment_term_id.id,
            'fiscal_position_id': self.fiscal_position_id.id or self.partner_invoice_id.property_account_position_id.id,
            'company_id': company_id,
            'user_id': self.user_id and self.user_id.id,
            'team_id': self.team_id.id,
            'transaction_ids': [(6, 0, self.transaction_ids.ids)],
        })
        return invoice_vals

    @api.multi
    def _create_analytic_account(self, prefix=None):
        for order in self:
            name = order.name
            if prefix:
                name = prefix + ": " + order.name
            if order.pricelist_id.currency_id.id:
                analytic = self.env['account.analytic.account'].create({
                    'name': name,
                    'code': order.client_order_ref,
                    'company_id': order.company_id.id,
                    'order_invoice_currency_id': order.pricelist_id.currency_id.id,
                    'partner_id': order.partner_id.id
                })
            else:
                analytic = self.env['account.analytic.account'].create({
                    'name': name,
                    'code': order.client_order_ref,
                    'company_id': order.company_id.id,
                    'partner_id': order.partner_id.id
                })
            order.analytic_account_id = analytic
    @api.depends('amount_untaxed', 'margin')
    def _compute_gp(self):
        for compute_gp in self:
            if compute_gp.amount_untaxed:
                compute_gp.gp = round((compute_gp.margin / compute_gp.amount_untaxed) * 100, 2)

    gp = fields.Float(string='GP%', store=True, readonly=True, compute='_compute_gp')

    amount_total = fields.Float(string='Total', store=True, readonly=True, digits=dp.get_precision('Account'), compute='_amount_all',
                                   track_visibility='always', track_sequence=6)


    amount_untaxed = fields.Float(string='Untaxed Amount', store=True, digits=dp.get_precision('Account'), readonly=True, compute='_amount_all',
                                   track_visibility='onchange', track_sequence=5)

class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    @api.multi
    def _prepare_invoice_line(self, qty):
        """
        Prepare the dict of values to create the new invoice line for a sales order line.

        :param qty: float quantity to invoice
        """
        self.ensure_one()
        res = {}
        product = self.product_id.with_context(force_company=self.company_id.id)
        account = product.property_account_income_id or product.categ_id.property_account_income_categ_id

        if not account and self.product_id:
            raise UserError(
                _('Please define income account for this product: "%s" (id:%d) - or for its category: "%s".') %
                (self.product_id.name, self.product_id.id, self.product_id.categ_id.name))

        fpos = self.order_id.fiscal_position_id or self.order_id.partner_id.property_account_position_id
        if fpos and account:
            account = fpos.map_account(account)
        res = {
            'name': self.name,
            'serial_number': self.serial_number,
            'sequence': self.sequence,
            'origin': self.order_id.name,
            'account_id': account.id,
            'price_unit': self.price_unit,
            'quantity': qty,
            'discount': self.discount,
            'uom_id': self.product_uom.id,
            'product_id': self.product_id.id or False,
            'invoice_line_tax_ids': [(6, 0, self.tax_id.ids)],
            'account_analytic_id': self.order_id.analytic_account_id.id,
            'analytic_tag_ids': [(6, 0, self.analytic_tag_ids.ids)],
            'display_type': self.display_type,
        }
        return res
    serial_number = fields.Char(string='Serial Number')
    product_uom_qty = fields.Float(string='Ordered Quantity', digits=dp.get_precision('Account'), required=True, default=1.00)

from odoo import api, fields, models, _
from odoo.exceptions import UserError
class SaleAdvancePaymentInv(models.TransientModel):
    _inherit = "sale.advance.payment.inv"

    @api.multi
    def _create_invoice(self, order, so_line, amount):
        inv_obj = self.env['account.invoice']
        ir_property_obj = self.env['ir.property']

        account_id = False
        if self.product_id.id:
            account_id = order.fiscal_position_id.map_account(self.product_id.property_account_income_id or self.product_id.categ_id.property_account_income_categ_id).id
        if not account_id:
            inc_acc = ir_property_obj.get('property_account_income_categ_id', 'product.category')
            account_id = order.fiscal_position_id.map_account(inc_acc).id if inc_acc else False
        if not account_id:
            raise UserError(
                _('There is no income account defined for this product: "%s". You may have to install a chart of account from Accounting app, settings menu.') %
                (self.product_id.name,))

        if self.amount <= 0.00:
            raise UserError(_('The value of the down payment amount must be positive.'))
        context = {'lang': order.partner_id.lang}
        if self.advance_payment_method == 'percentage':
            amount = order.amount_untaxed * self.amount / 100
            name = _("Down payment of %s%%") % (self.amount,)
        else:
            amount = self.amount
            name = _('Down Payment')
        del context
        taxes = self.product_id.taxes_id.filtered(lambda r: not order.company_id or r.company_id == order.company_id)
        if order.fiscal_position_id and taxes:
            tax_ids = order.fiscal_position_id.map_tax(taxes, self.product_id, order.partner_shipping_id).ids
        else:
            tax_ids = taxes.ids

        invoice = inv_obj.create({
            'name': order.client_order_ref or order.name,
            'po_number': order.po_number,
            'vendor_number': order.vendor_number,
            'origin': order.name,
            'type': 'out_invoice',
            'reference': False,
            'account_id': order.partner_id.property_account_receivable_id.id,
            'partner_id': order.partner_invoice_id.id,
            'partner_shipping_id': order.partner_shipping_id.id,
            'invoice_line_ids': [(0, 0, {
                'serial_number': order.serial_number,
                'name': name,
                'origin': order.name,
                'account_id': account_id,
                'price_unit': amount,
                'quantity': 1.0,
                'discount': 0.0,
                'uom_id': self.product_id.uom_id.id,
                'product_id': self.product_id.id,
                'sale_line_ids': [(6, 0, [so_line.id])],
                'invoice_line_tax_ids': [(6, 0, tax_ids)],
                'analytic_tag_ids': [(6, 0, so_line.analytic_tag_ids.ids)],
                'account_analytic_id': order.analytic_account_id.id or False,
            })],
            'currency_id': order.pricelist_id.currency_id.id,
            'payment_term_id': order.payment_term_id.id,
            'fiscal_position_id': order.fiscal_position_id.id or order.partner_id.property_account_position_id.id,
            'team_id': order.team_id.id,
            'user_id': order.user_id.id,
            'company_id': order.company_id.id,
            'comment': order.note,
        })
        invoice.compute_taxes()
        invoice.message_post_with_view('mail.message_origin_link',
                    values={'self': invoice, 'origin': order},
                    subtype_id=self.env.ref('mail.mt_note').id)
        return invoice
