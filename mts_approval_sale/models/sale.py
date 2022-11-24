# -*- coding:utf-8 -*-
# import re
# import calendar

from odoo import models, fields, api, _
from odoo.exceptions import UserError
import time
from odoo.tools import float_is_zero, float_compare

DATE_FMT = "%Y-%m-%d"
email_from = "Odoo <matrix@mtscloud.com>"
message_data = dict(email_from=email_from)


class QuotedOrder(models.Model):
    _name = 'sale.order'
    _inherit = ['sale.order', 'mail.thread', 'mail.activity.mixin', 'approval.request']

    closed_reason = fields.Many2one('sale.closed.reason', string='Closed Reason', index=True, track_visibility='onchange',prefetch=False)
    sale_id = fields.Many2one('sale.order', string='Renewal Sale Order', index=True, track_visibility='onchange',prefetch=False)

    @api.multi
    def action_reopen(self):
        return self.write({'state': 'sale'})

    @api.multi
    def action_terminate(self):
        return self.write({'state': 'terminate'})

    @api.multi
    def print_quotation(self):
        self.filtered(lambda s: s.state == 'quotation approved').write({'state': 'sent'})

        return self.env.ref('mts_sale_quotation_order_invoicing_report_extend.action_report_salequotation')\
            .with_context(discard_logo_check=True).report_action(self)

    @api.multi
    def action_set_lost(self):
        """ Lost semantic: probability = 0, active = False """
        return self.write({'state': "close"})

    state = fields.Selection([

        ('draft', 'Quotation'),

        ('quotation approval', 'Quotation Approval'),
        ('refuse quotation', 'Refuse Quotation'),
        ('quotation approved', 'Quotation Approved'),

        ('sent', 'Quotation Sent'),

        ('order approval', 'Order Approval'),
        ('refuse order', 'Refuse Order'),

        ('sale', 'Sales Order'),

        ('done', 'Locked'),
        ('cancel', 'Cancelled'),
        ('terminate', 'Terminated'),
        ('close', 'Closed'),
    ], string='Status', readonly=True, copy=False, index=True, track_visibility='onchange', track_sequence=3, default='draft')

    # state,  _track_subtype() 改变 下面会有提示信息发邮件 所以注释掉！
    @api.multi
    def _track_subtype(self, init_values):
        # self.ensure_one()
        # if 'state' in init_values and self.state == 'sale':
        #     return 'sale.mt_order_confirmed'
        # elif 'state' in init_values and self.state == 'sent':
        #     return 'sale.mt_order_sent'
        # return super(QuotedOrder, self)._track_subtype(init_values)
        return False

    approval_list = fields.Many2one("approval.approval", string="Approval List", default=None, required=True,
                                    domain=[('approval_type.model_id.model', '=', 'sale.order')])
    # approval_flow_id = fields.Many2one('approval.flow', string="Flow")
    # approver = fields.Many2one(related='approval_flow_id.approver', string="Approver")
    employee_id = fields.Many2one('hr.employee',  store=True, string="Employee", required=True, readonly=True,
            default=lambda self: self.env['hr.employee'].sudo().search([('user_id', '=', self.env.uid)], limit=1))

    approver = fields.Many2one('res.users', compute='_compute_approver', string="Approver", default=None, store=True)
    current_user_is_approver = fields.Boolean(string='Current user is approver?', compute='_compute_current_user_is_approver')

    @api.depends('approval_list', 'approval_flow_id')
    def _compute_approver(self):
        for list in self:
            if not list.approval_list:
                list.approver = list.employee_id.parent_id.user_id
            elif list.approval_flow_id:
                list.approver = list.approval_flow_id.approver
            else:
                list.approver = None

    current_user_is_requester = fields.Boolean(string='Current user is requester?',
                                               compute='_compute_current_user_is_requester')
    # approval_approbations = fields.One2many('approval.flow.approbation', 'sale', string='Approvals msg',
    #                                         readonly=True)
    approval_approbations = fields.One2many('sale.order.approval.approbation', 'sale_order_id', string='Approvals', readonly=True)

    # refuse_reason = fields.Text("", readonly=True)

    # @api.onchange('approval_list')
    # def _onchange_approval_list(self):
    #     if self.approval_list.flow:
    #         flow = self.approval_list.flow.filtered(lambda x: x.require_opt == 'Required')
    #         self.approval_flow_id = flow.sorted('sequence')[0]

    # effective_date = fields.Datetime(string='Effective Date')
    Effective_Date = fields.Datetime(string='Effective Date')
    end_date = fields.Datetime(string='End Date')

    @api.multi
    def action_confirm_approval(self):
        self.ensure_one()

        if self.po_number == 'N/A':
            raise UserError(
                _('Please fill in PO Number !'))

        if not self.partner_id.child_ids:
            raise UserError(
                _('Please fill in the customer contact!'))

        if self.filtered(lambda QuotedOrder: QuotedOrder.state != 'sent' and QuotedOrder.state != 'quotation approved'):
            raise UserError(
                _('Sale request must be in Draft state approval ("To Submit") in order to confirm it.'))
        # self.message_subscribe(partner_ids=self.sudo().approver.partner_id.ids)

        template_id = self.sudo().env.ref('mts_approval_sale.email_submit_order_approval_template')
        template_id.send_mail(self.id, force_send=True)
        # msg = _('Submitted for review.')
        # self.message_post(body=msg)
        # self.sudo().message_post_with_view('mts_approval_sale.order_generated_notification', **message_data)
        self.write({'state': 'order approval'})
        return True

    @api.multi
    def action_confirm_approval_quotation(self):
        # self.ensure_one()

        if not self.partner_id.child_ids:
            raise UserError(
                _('Please fill in the customer contact!'))

        if self.filtered(lambda QuotedOrder: QuotedOrder.state != 'draft'):
            raise UserError(
                _('Sale request must be in Draft state approval ("To Submit") in order to confirm it.'))
        # self.message_subscribe(partner_ids=self.sudo().approver_quotation.partner_id.ids)
        template_id = self.sudo().env.ref('mts_approval_sale.email_submit_quotation_approval_template')
        template_id.send_mail(self.id, force_send=True)
        self.write({'state': 'quotation approval'})
        # msg = _('Submitted for review.')
        # self.message_post(body=msg)
        # self.sudo().message_post_with_view('mts_approval_sale.quotation_generated_notification', **message_data)

        return True

    @api.multi
    def action_approve(self):
        self.ensure_one()
        if not self.current_user_is_approver:
            return

        next_approval_flow = self.next_approver()
        if not next_approval_flow:
            self.action_validate()
        else:
            self.write({'state': 'order approval', 'approval_flow_id': next_approval_flow.id})
            self.env['sale.order.approval.approbation'].create(
                {'sale_order_id': self.id, 'approver': self.env.uid, 'status': 'approved', 'date': fields.Datetime.now()})
            self.activity_update()
            # template_id = self.sudo().env.ref('mts_approval_sale.email_approval_order_approval_template')
            # template_id.send_mail(self.id, force_send=True)

            # self.message_subscribe(partner_ids=next_approval_flow.sudo().approver.partner_id.ids)
            # msg = _('Approved')
            # self.message_post(body=msg)
            # self.sudo().message_post_with_view('mts_approval_sale.order_nextapprover_notification', **message_data)
    @api.multi
    def action_approve_quotation(self):
        self.ensure_one()
        if not self.current_user_is_approver_quotation:
            return

        next_approval_flow = self.next_approver_quotation()
        if not next_approval_flow:
            self.action_validate_quotation()
        else:
            self.write({'state': 'quotation approval', 'approval_flow_id_quotation': next_approval_flow.id})
            self.env['sale.order.approval.approbation'].create(
                {'sale_quotation_id': self.id, 'approver': self.env.uid, 'status': 'approved',
                 'date': fields.Datetime.now()})
            self.activity_update()
            # template_id = self.sudo().env.ref('mts_approval_sale.email_approval_quotation_approval_template')
            # template_id.send_mail(self.id, force_send=True)

            # self.message_subscribe(partner_ids=next_approval_flaction_draft_approvalow.sudo().approver.partner_id.ids)
            # msg = _('Approved')
            # self.message_post(body=msg)
            # self.sudo().message_post_with_view('mts_approval_sale.quotation_nextapprover_notification', **message_data)

    @api.multi
    def action_confirm(self):
        if self._get_forbidden_state_confirm() & set(self.mapped('state')):
            raise UserError(_(
                'It is not allowed to confirm an order in the following states: %s'
            ) % (', '.join(self._get_forbidden_state_confirm())))

        # for order in self.filtered(lambda order: order.partner_id not in order.message_partner_ids):
        #     order.message_subscribe([order.partner_id.id])
        # self.write({
        #     'state': 'sale',
        #     'confirmation_date': fields.Datetime.now()
        # })
        self._action_confirm()
        if self.env['ir.config_parameter'].sudo().get_param('sale.auto_done_setting'):
            self.action_done()
        return True
    @api.multi
    def action_validate(self):
        self.ensure_one()
        self.write({
            'approval_flow_id': None,
            'state': 'sale',
            'confirmation_date': fields.Datetime.now()
        })
        self.action_confirm()

        self.env['sale.order.approval.approbation'].create(
            {'sale_order_id': self.id, 'approver': self.env.uid, 'status': 'approved', 'date': fields.Datetime.now()})
        self.activity_update()
        template_id = self.sudo().env.ref('mts_approval_sale.email_approved_order_approval_template')
        template_id.send_mail(self.id, force_send=True)
        # msg = _('Approved')
        # self.message_post(body=msg)
        # self.sudo().message_post_with_view('mts_approval_sale.order_done_notification', **message_data)

    @api.multi
    def action_validate_quotation(self):
        self.ensure_one()
        self.write({'approval_flow_id_quotation': None, 'state': 'quotation approved', 'flow_sign': 'order'})
        # self.write({'approval_flow_id': None, 'state': 'order approved'})
        self.env['sale.order.approval.approbation'].create(
            {'sale_quotation_id': self.id, 'approver': self.env.uid, 'status': 'approved', 'date': fields.Datetime.now()})

        self.activity_update()
        template_id = self.sudo().env.ref('mts_approval_sale.email_approved_quotation_approval_template')
        template_id.send_mail(self.id, force_send=True)
        # msg = _('Approved')
        # self.message_post(body=msg)
        # self.sudo().message_post_with_view('mts_approval_sale.quotation_done_notification', **message_data)

    @api.multi
    def action_refuse(self, reason=''):
        self.ensure_one()
        if self.filtered(lambda QuotedOrder: QuotedOrder.state != 'order approval'):
            raise UserError(_('Order request must be in Confirm state approval.'))
        flow = self.approval_list.flow.filtered(lambda x: x.require_opt == 'Required')

        if flow:
            self.approval_flow_id = flow.sorted('sequence')[0]  # 重新指定审核flow
        else:
            self.approver = self.employee_id.parent_id.user_id

        # self.approval_flow_id = flow.sorted('sequence')[0]  # 重新指定审核flow
        self.write({'state': 'refuse order'})
        self.env['sale.order.approval.approbation'].create(
            {'sale_order_id': self.id, 'approver': self.env.uid, 'status': 'Rejected',
             'date': fields.Datetime.now(), 'comments': reason
             })
        msg = _('Refused due to reason: {}'.format(reason))
        self.refuse_reason = reason
        template_id = self.sudo().env.ref('mts_approval_sale.email_refuse_order_approval_template')
        template_id.send_mail(self.id, force_send=True)
        # msg = _('Refused due to reason: {}'.format(reason))
        # self.refuse_reason = reason
        # self.message_post(body=msg)
        # self.sudo().message_post_with_view('mts_approval_sale.order_refuse_notification', **message_data)
        return True

    @api.multi
    def action_refuse_quotation(self, reason=''):
        self.ensure_one()
        if self.filtered(lambda QuotedOrder: QuotedOrder.state != 'quotation approval'):
            raise UserError(_('Sale request must be in Confirm state approval.'))
        flow = self.approval_list_quotation.flow.filtered(lambda x: x.require_opt == 'Required')

        if flow:
            self.approval_flow_id_quotation = flow.sorted('sequence')[0]  # 重新指定审核flow
        else:
            self.approver_quotation = self.employee_id.parent_id.user_id

        # self.approval_flow_id_quotation = flow.sorted('sequence')[0]  # 重新指定审核flow
        self.write({'state': 'refuse quotation'})
        self.env['sale.order.approval.approbation'].create(
            {'sale_quotation_id': self.id, 'approver': self.env.uid, 'status': 'Rejected',
             'date': fields.Datetime.now(), 'comments': reason
             })
        # msg = _('Refused due to reason: {}'.format(reason))
        self.refuse_reason_quotation = reason
        template_id = self.sudo().env.ref('mts_approval_sale.email_refuse_quotation_approval_template')
        template_id.send_mail(self.id, force_send=True)
        # msg = _('Refused due to reason: {}'.format(reason))
        # self.refuse_reason = reason
        # self.message_post(body=msg)
        # self.sudo().message_post_with_view('mts_approval_sale.quotation_refuse_notification', **message_data)
        return True

    @api.multi
    def action_draft_approval(self):
        self.ensure_one()
        # if self.filtered(lambda QuotedOrder:
        #                  (QuotedOrder.state != 'refuse order' and QuotedOrder.state != 'order approval')):
        #     raise UserError(_('sales request must be in Confirm or Refuse state approval.'))
        flow = self.approval_list.flow.filtered(lambda x: x.require_opt == 'Required')
        if flow:
            self.approval_flow_id = flow.sorted('sequence')[0]  # 重新指定审核flow)
        else:
            self.approver = self.employee_id.parent_id.user_id
        # self.write({'state': 'draft'})
        self.write({'state': 'sent'})

        # template_id = self.sudo().env.ref('mts_approval_sale.reset_to_draft_order_approval_template')
        # template_id.send_mail(self.id, force_send=True)
        # msg = _('Changed it to draft to resubmit.')
        # self.message_post(body=msg)
        return True

    @api.multi
    def action_reset_new_quotation(self):
        self.ensure_one()
        if self.filtered(lambda QuotedOrder:
                         (QuotedOrder.state != 'refuse order' and QuotedOrder.state != 'order approval')):
            raise UserError(_('sales request must be in Confirm or Refuse state approval.'))
        flow = self.approval_list.flow.filtered(lambda x: x.require_opt == 'Required')
        # self.approval_list = None
        # self.approval_flow_id = None
        # self.approval_list_quotation = None
        # self.approval_flow_id_quotation = None
        # self.flow_sign = 'quotation'
        # self.approval_flow_id = flow.sorted('sequence')[0]  # 重新指定审核flow)
        self.write({'state': 'draft', 'approval_list': None, 'approval_flow_id': None, 'approval_list_quotation': None, 'approval_flow_id_quotation': None, 'flow_sign': None})

        # template_id = self.sudo().env.ref('mts_approval_sale.reset_to_new_quotation_approval_template')
        # template_id.send_mail(self.id, force_send=True)
        # msg = _('Changed it to draft to resubmit.')
        # self.message_post(body=msg)
        return True

    @api.multi
    def action_draft_approval_quotation(self):
        self.ensure_one()
        # if self.filtered(lambda QuotedOrder:
        #                  (QuotedOrder.state != 'refuse quotation' and QuotedOrder.state != 'quotation approval')):
        #     raise UserError(_('sales request must be in Confirm or Refuse state approval.'))
        flow = self.approval_list_quotation.flow.filtered(lambda x: x.require_opt == 'Required')
        if flow:
            self.approval_flow_id_quotation = flow.sorted('sequence')[0]  # 重新指定审核flow)
        else:
            self.approver_quotation = self.employee_id.parent_id.user_id
        self.write({'state': 'draft'})
        # 发邮件 重新提交审批流 提醒create_uid
        # template_id = self.sudo().env.ref('mts_approval_sale.reset_to_draft_quotation_approval_template')
        # template_id.send_mail(self.id, force_send=True)
        # msg = _('Changed it to draft to resubmit.')
        # self.message_post(body=msg)
        return True

    @api.multi
    def draft_payslip_run(self):
        self.ensure_one()
        flow = self.approval_list.flow.filtered(lambda x: x.require_opt == 'Required')
        self.approval_flow_id = flow.sorted('sequence')[0]  # 重新指定审核flow
        self.write({'state_approval': 'draft'})
        msg = _('Changed it to draft to resubmit.')
        self.message_post(body=msg)
        return True

    def _compute_current_user_is_requester(self):
        self.ensure_one()
        if self.create_uid == self.env.user:
            self.current_user_is_requester = True
            # print(222222222222222222222222222222222222222222)
            # print(self.current_user_is_requester_quotation)
            # print(22222222222222222222222222222222222222222)
        else:
            # print(33333333333333333333333)
            self.current_user_is_requester = False

    def _compute_current_user_is_requester_quotation(self):
        self.ensure_one()
        if self.create_uid == self.env.user:
            self.current_user_is_requester_quotation = True
        else:
            self.current_user_is_requester_quotation = False

    def _compute_current_user_is_approver(self):
        self.ensure_one()
        if self.approver == self.env.user:
            self.current_user_is_approver = True
        else:
            self.current_user_is_approver = False

    def _compute_current_user_is_approver_quotation(self):
        self.ensure_one()
        if self.approver_quotation == self.env.user:
            self.current_user_is_approver_quotation = True
        else:
            self.current_user_is_approver_quotation = False

    # def next_approver(self):
    #     self.ensure_one()
    #     if len(self.approval_list.flow.filtered(lambda x: x.sequence == self.approval_flow_id.sequence)) > 1:
    #         other_flow = self.approval_list.flow.filtered(
    #             lambda
    #                 x: x.id > self.approval_flow_id.id and x.sequence == self.approval_flow_id.sequence and x.require_opt == 'Required')
    #         if not other_flow:
    #             other_flow = self.approval_list.flow.filtered(
    #                 lambda x: x.sequence > self.approval_flow_id.sequence and x.require_opt == 'Required')
    #     else:
    #         other_flow = self.approval_list.flow.filtered(
    #             lambda x: x.sequence > self.approval_flow_id.sequence and x.require_opt == 'Required')
    #     if not other_flow:
    #         return False
    #     else:
    #         return other_flow.sorted('sequence')[0]

    def next_approver_quotation(self):
        self.ensure_one()
        if len(self.approval_list_quotation.flow.filtered(lambda x: x.sequence == self.approval_flow_id_quotation.sequence)) > 1:
            other_flow = self.approval_list_quotation.flow.filtered(
                lambda
                    x: x.id > self.approval_flow_id_quotation.id and x.sequence == self.approval_flow_id_quotation.sequence and x.require_opt == 'Required')
            if not other_flow:
                other_flow = self.approval_list_quotation.flow.filtered(
                    lambda x: x.sequence > self.approval_flow_id_quotation.sequence and x.require_opt == 'Required')
        else:
            other_flow = self.approval_list_quotation.flow.filtered(
                lambda x: x.sequence > self.approval_flow_id_quotation.sequence and x.require_opt == 'Required')
        if not other_flow:
            return False
        else:
            return other_flow.sorted('sequence')[0]

    approval_list_quotation = fields.Many2one("approval.approval", string="Approval List", default=None, required=True,
                                    domain=[('approval_type.model_id.model', '=', 'sale.order')])
    approval_flow_id_quotation = fields.Many2one('approval.flow', string="Flow")
    # approver_quotation = fields.Many2one(related='approval_flow_id_quotation.approver', string="Approver")
    approver_quotation = fields.Many2one('res.users', compute='_compute_quotation_approver', string="Approver", default=None, store=True)
    current_user_is_approver_quotation = fields.Boolean(string='Current user is approver?',
                                                        compute='_compute_current_user_is_approver_quotation')
    current_user_is_requester_quotation = fields.Boolean(string='Current user is requester?',
                                                         compute='_compute_current_user_is_requester_quotation')
    approval_approbations_quotation = fields.One2many('sale.order.approval.approbation', 'sale_quotation_id', string='Approvals msg',
                                                      readonly=True)
    refuse_reason_quotation = fields.Text("", readonly=True)

    # flow_sign = fields.Char(string='Flow Sign', default='quotation')

    @api.onchange('approval_list_quotation')
    def _onchange_approval_list_quoted(self):
        if self.approval_list_quotation.flow:
            flow = self.approval_list_quotation.flow.filtered(lambda x: x.require_opt == 'Required')
            self.approval_flow_id_quotation = flow.sorted('sequence')[0]

    @api.depends('approval_list_quotation', 'approval_flow_id_quotation')
    def _compute_quotation_approver(self):
        for list in self:
            if not list.approval_list_quotation:
                list.approver_quotation = list.employee_id.parent_id.user_id
            elif list.approval_flow_id_quotation:
                list.approver_quotation = list.approval_flow_id_quotation.approver
            else:
                list.approver_quotation = None

    @api.multi
    @api.returns('mail.message', lambda value: value.id)
    def message_post(self, **kwargs):
        if self.env.context.get('mark_so_as_sent'):
            self.filtered(lambda o: o.state == 'quotation approved').with_context(tracking_disable=True).write({'state': 'sent'})
            self.env.user.company_id.set_onboarding_step_done('sale_onboarding_sample_quotation_state')
        return super(QuotedOrder, self.with_context(mail_post_autofollow=True)).message_post(**kwargs)

    def back_quotation_email_cc(self):
        optional_flows = self.approval_list_quotation.flow.filtered(
            lambda x: x.require_opt == 'Optional')
        cc = ''
        for o in optional_flows:
            cc += o.approver.partner_id.email + ','
        result = cc
            # 'recipient_ids': [(6, 0, [self.create_uid.partner_id.id])],
        return result

    def back_order_email_cc(self):
        optional_flows = self.approval_list.flow.filtered(
            lambda x: x.require_opt == 'Optional')
        cc = ''
        for o in optional_flows:
            cc += o.approver.partner_id.email + ','
        result = cc
        return result

    @api.multi
    def action_draft(self):
        # draft,quotation approval,quotation approved,refuse quotation,sent,order approval,sale,refuse order，sale
        orders = self.filtered(lambda s: s.state in ['draft', 'quotation approval', 'quotation approved', 'refuse quotation', 'cancel', 'sent', 'order approval', 'sale, refuse order'])
        return orders.write({
            'approval_list_quotation': None,
            'approver_quotation': None,
            'approval_list': None,
            'approver': None,
            'approval_approbations_quotation': None,
            'approval_approbations': None,
            'approval_flow_id': None,
            'approval_flow_id_quotation': None,
            'state': 'draft',
            'signature': False,
            'signed_by': False,
        })

    @api.multi
    def action_quotation_send(self):
        '''
        This function opens a window to compose an email, with the edi sale template message loaded by default
        '''
        self.ensure_one()
        ir_model_data = self.env['ir.model.data']
        try:
            if self.state == 'quotation approved' or self.state == 'sent':
                template_id = ir_model_data.get_object_reference('mts_approval_sale', 'email_template_edi_sale_congxieQuotation')[1]
            elif self.state == 'sale':
                template_id = ir_model_data.get_object_reference('mts_approval_sale', 'email_template_edi_sale_congxieOrder')[1]

        except ValueError:
            template_id = False
        try:
            compose_form_id = ir_model_data.get_object_reference('mail', 'email_compose_message_wizard_form')[1]
        except ValueError:
            compose_form_id = False
        lang = self.env.context.get('lang')
        template = template_id and self.env['mail.template'].browse(template_id)
        if template and template.lang:
            lang = template._render_template(template.lang, 'sale.order', self.ids[0])
        ctx = {
            'default_model': 'sale.order',
            'default_res_id': self.ids[0],
            'default_use_template': bool(template_id),
            'default_template_id': template_id,
            'default_composition_mode': 'comment',
            'mark_so_as_sent': True,
            'model_description': self.with_context(lang=lang).type_name,
            'custom_layout': "mail.mail_notification_paynow",
            'proforma': self.env.context.get('proforma', False),
            'force_email': True
        }
        return {
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'mail.compose.message',
            'views': [(compose_form_id, 'form')],
            'view_id': compose_form_id,
            'target': 'new',
            'context': ctx,
        }

    # 下面加一条记录, activity_schedule() 会发邮件给下一个人或指定的人
    def activity_update(self):
        for quo_request in self.filtered(lambda req: req.state == 'quotation approval'):
            self.activity_schedule('mts_approval_sale.mail_act_quotation_approval', user_id=quo_request.sudo()._get_responsible_for_quotation_approval().id or self.env.user.id)
            # self.activity_schedule('mts_approval_sale.mail_act_quotation_approval', user_id=quo_request.sudo().approver_quotation.id)

        for ord_request in self.filtered(lambda req: req.state == 'order approval'):
            self.activity_schedule('mts_approval_sale.mail_act_sale_order_approval', user_id=ord_request.sudo()._get_responsible_for_order_approval().id or self.env.user.id)
            # self.activity_schedule('mts_approval_sale.mail_act_sale_order_approval', user_id=ord_request.sudo().approver.id)

        self.filtered(lambda req: req.state == 'quotation approved').activity_feedback(
            ['mts_approval_sale.mail_act_quotation_approval'])

        self.filtered(lambda req: req.state == 'refuse quotation').activity_unlink(
            ['mts_approval_sale.mail_act_quotation_approval'])

        self.filtered(lambda req: req.state == 'order approved').activity_feedback(
            ['mts_approval_sale.mail_act_sale_order_approval'])

        self.filtered(lambda req: req.state == 'refuse order').activity_unlink(
            ['mts_approval_sale.mail_act_sale_order_approval'])

    def _get_responsible_for_quotation_approval(self):
        if self.approver_quotation:
            return self.approver_quotation
        elif self.employee_id.parent_id.user_id:
            return self.employee_id.parent_id.user_id
        elif self.employee_id.department_id.manager_id.user_id:
            return self.employee_id.department_id.manager_id.user_id
        return self.env['res.users']

    def _get_responsible_for_order_approval(self):
        if self.approver:
            return self.approver
        elif self.employee_id.parent_id.user_id:
            return self.employee_id.parent_id.user_id
        elif self.employee_id.department_id.manager_id.user_id:
            return self.employee_id.department_id.manager_id.user_id
        return self.env['res.users']

class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    come_from = fields.Char(string='Come From', default='sale order')

class SaleOrderApprovalApprobation(models.Model):
    _name = "sale.order.approval.approbation"
    _inherit = ['approval.approbation']
    _description = "Keep current approved user list for request"
    _order = "sequence"

    sale_order_id = fields.Many2one('sale.order', string="Sale Order")
    sale_quotation_id = fields.Many2one('sale.order', string="Sale Quotation")

class CLoseReason(models.Model):
    _name = "sale.closed.reason"
    _description = 'Opp. cLose Reason'

    name = fields.Char('Name', required=True, translate=True)
    active = fields.Boolean('Active', default=True)

class AccountAnalyticAccount(models.Model):
    _inherit = 'account.analytic.account'

    order_count = fields.Integer(
        compute="_order_count",
    )

    @api.multi
    @api.depends()
    def _order_count(self):
        for rec in self:
            rec.ensure_one()
            sale_order_line = self.env['sale.order'].search([
                ('analytic_account_id', '=', rec.id),
            ])
            rec.order_count = len(sale_order_line)

