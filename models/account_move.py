# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from datetime import datetime
 
class AccountMove(models.Model):
    _inherit ='account.move'

    operation_unit_id = fields.Many2one(
        'operation.unit',copy=False )

    
    from_other_order = fields.Boolean(
        compute='_compute_from_other_order',
     )

    @api.depends('invoice_line_ids')
    def _compute_from_other_order(self):
        for move in self:
            
            move.from_other_order =  False

        
   
    allowed_ou_domain = fields.Char(compute="get_allowed_ou_domain")

    @api.depends('company_id','invoice_user_id')
    def get_allowed_ou_domain(self):
        for rec in self:
            rec.allowed_ou_domain = [('id','in',self.env.user.ou_config_ids.filtered(lambda x: x.company_id.id == rec.company_id.id).allowed_ou_ids.ids)]

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)

        company_id = res.get('company_id', self.env.company.id)

        if not res.get('operation_unit_id'):
            ou = self.env.user.ou_config_ids.filtered(
                lambda x: x.company_id.id == company_id
            ).default_ou_id

            if ou:
                res['operation_unit_id'] = ou.id

        return res
    
    @api.onchange('company_id')
    def _onchange_company_id_set_ou(self):
        for rec in self:
            if not rec.company_id:
                rec.operation_unit_id = False
                return

            # OU الحالي غير تابع للشركة
            if rec.operation_unit_id and rec.operation_unit_id.company_id != rec.company_id:
                rec.operation_unit_id = False

            # تعيين OU افتراضي
            if not rec.operation_unit_id:
                ou = self.env.user.ou_config_ids.filtered(
                    lambda x: x.company_id == rec.company_id
                ).default_ou_id

                if ou:
                    rec.operation_unit_id = ou

    allow_modify_ou_flag = fields.Boolean(
        default=lambda self: self._default_allow_modify_ou_flag(),
        compute="_check_allow_modify_ou_flag",
    )
    def _default_allow_modify_ou_flag(self):
        
        return self.user_has_groups('yousentech_invoicing_ou.group_allow_modify_ou')

    def _check_allow_modify_ou_flag(self):
        
        for rec in self:
            rec.allow_modify_ou_flag = self.user_has_groups('yousentech_invoicing_ou.group_allow_modify_ou')


    @api.model
    def create(self, vals):
       
        if not vals.get('operation_unit_id'):
            vals['operation_unit_id'] =  self.env.user.ou_config_ids.filtered(lambda x: x.company_id.id == vals.get('company_id')).default_ou_id.id

        return super().create(vals)
 
   
    @api.constrains('invoice_line_ids', 'operation_unit_id')
    def _check_single_ou(self):
        for move in self:
            ous = self.env['operation.unit']

            # 1️⃣ OU من الفاتورة نفسها
            if move.operation_unit_id:
                ous |= move.operation_unit_id

 
            # 2️⃣ OU من سطور الفاتورة
            for line in move.invoice_line_ids:
                if line.operation_unit_id:
                    ous |= line.operation_unit_id
  
            ous = ous.filtered(lambda x: x)

            if len(ous) > 1:
                raise ValidationError(
                    _('You cannot mix multiple Operation Units in one invoice.')
                )

                
    @api.constrains('operation_unit_id')
    def _check_ou_required(self):
        for rec in self:
            if not rec.operation_unit_id:
                raise ValidationError(
                    'move Operation Unit is required'
                )
 
    def _get_outstanding_info_JSON(self):
        self.ensure_one()
        result = super()._get_outstanding_info_JSON()
    
        # لو ما فيه OU على الفاتورة أو ما فيه مدفوعات
        if not self.operation_unit_id or not result or not result.get('content'):
            return result

        invoice_ou_id = self.operation_unit_id.id
        filtered_content = []

        for line in result['content']:
            aml_id = line.get('line_id')
            if not aml_id:
                continue

            aml = self.env['account.move.line'].browse(aml_id)

            # نعرض فقط المدفوعات التابعة لنفس OU
            if aml.operation_unit_id and aml.operation_unit_id.id == invoice_ou_id:
                filtered_content.append(line)

        result['content'] = filtered_content
        return result
     
    @api.constrains('operation_unit_id', 'company_id')
    def _check_operation_unit_validity(self):
        for move in self:
            ou = move.operation_unit_id
            user = self.env.user

            if not ou:
                raise ValidationError("Operation Unit is required on this document.")
 
            if ou.company_id != move.company_id:
                raise ValidationError(
                    "The selected Operation Unit does not belong to the same company as this document."
                ) 

            if user.ou_config_ids.filtered(lambda x: x.company_id.id == move.company_id.id).allowed_ou_ids and ou not in user.ou_config_ids.filtered(lambda x: x.company_id.id == move.company_id.id).allowed_ou_ids:

                raise ValidationError(
                    "The selected Operation Unit is not allowed for the current user."
                )

    def action_post(self):
        for move in self:
            if not move.operation_unit_id:
                raise ValidationError(
                    'Operation Unit is required before posting the accounting entry.'
                )
            move._check_operation_unit_validity()
        return super().action_post()

    @api.constrains('operation_unit_id', 'company_id')
    def _check_ou_company(self):
        for rec in self:
            if rec.operation_unit_id and rec.company_id:
                if rec.operation_unit_id.company_id != rec.company_id:
                    raise ValidationError(
                        "Operation Unit must belong to the selected company."
                    )
 
 
    @api.constrains('operation_unit_id')
    def _check_ou_change_after_reconcile(self):
        for move in self:
            if move.line_ids.filtered(lambda l: l.reconciled):
                raise ValidationError(
                    'You cannot change Operation Unit on reconciled entries.'
                )
    
    def _compute_payments_widget_to_reconcile_info(self):
        for move in self:
            move.invoice_outstanding_credits_debits_widget = False
            move.invoice_has_outstanding = False

            if move.state != 'posted' \
                    or move.payment_state not in ('not_paid', 'partial') \
                    or not move.is_invoice(include_receipts=True):
                continue

            pay_term_lines = move.line_ids\
                .filtered(lambda line: line.account_id.account_type in ('asset_receivable', 'liability_payable'))
            ou_list =[]
            ou_list.append(move.operation_unit_id.id)
            for ou_id in self.env.user.ou_config_ids.filtered(lambda x: x.company_id.id == move.company_id.id).allowed_ou_ids.filtered(lambda x: x.share_ou).ids:
                ou_list.append(ou_id)

            domain = [
                ('account_id', 'in', pay_term_lines.account_id.ids),
                ('parent_state', '=', 'posted'),
                ('partner_id', '=', move.commercial_partner_id.id),
                ('reconciled', '=', False),
                 '|', ('move_id.operation_unit_id','in',ou_list),('move_id.operation_unit_id','=',False) ,
                '|', ('amount_residual', '!=', 0.0), ('amount_residual_currency', '!=', 0.0),
              
            ]

            payments_widget_vals = {'outstanding': True, 'content': [], 'move_id': move.id}

            if move.is_inbound():
                domain.append(('balance', '<', 0.0))
                payments_widget_vals['title'] = _('Outstanding credits')
            else:
                domain.append(('balance', '>', 0.0))
                payments_widget_vals['title'] = _('Outstanding debits')

            for line in self.env['account.move.line'].search(domain):

                if line.currency_id == move.currency_id:
                    # Same foreign currency.
                    amount = abs(line.amount_residual_currency)
                else:
                    # Different foreign currencies.
                    amount = line.company_currency_id._convert(
                        abs(line.amount_residual),
                        move.currency_id,
                        move.company_id,
                        line.date,
                    )

                if move.currency_id.is_zero(amount):
                    continue

                payments_widget_vals['content'].append({
                    'journal_name': line.ref or line.move_id.name,
                    'amount': amount,
                    'currency_id': move.currency_id.id,
                    'id': line.id,
                    'move_id': line.move_id.id,
                    'date': fields.Date.to_string(line.date),
                    'account_payment_id': line.payment_id.id,
                })

            if not payments_widget_vals['content']:
                continue

            move.invoice_outstanding_credits_debits_widget = payments_widget_vals
            move.invoice_has_outstanding = True

 
class AccountPaymentRegister(models.TransientModel):
    _inherit = "account.payment.register"

    operation_unit_id = fields.Many2one(
        'operation.unit',
        string='Operation Unit',
        readonly=True,
        related='line_ids.move_id.operation_unit_id',
        copy=False )

    def _init_payments(self, to_process, edit_mode=False):
    
        for vals in to_process:
            create_vals = vals.get('create_vals', {})

            if self.operation_unit_id:
                create_vals['operation_unit_id'] = self.operation_unit_id.id

       
        return super()._init_payments(to_process, edit_mode=edit_mode)

    
  



class AccountMoveLine(models.Model):
    _inherit = 'account.move.line' 

    operation_unit_id = fields.Many2one(
        'operation.unit',
        string='Operation Unit',
        readonly=True,
        related='move_id.operation_unit_id',
        store=True,
        copy=False
    )
 
    def reconcile(self):
        for rec in self:
            print("payment_id*********************",rec.payment_id)
            print("payment_id move_id*********************",rec.move_id)

            print("payment_id********operation_unit_id*************",rec.payment_id.operation_unit_id.id)
            print("payment_id move_id*********operation_unit_id************",rec.move_id.operation_unit_id.id)

            if rec.payment_id:
                if not (rec.payment_id.operation_unit_id.id == rec.move_id.operation_unit_id.id):
                    raise ValidationError(
                            'You cannot reconcile entries from different Operation Units.111'
                        )
            
                ous = self.mapped('operation_unit_id').filtered(lambda x: x)
                print("ous*********************",ous.filtered(lambda x: not x.share_ou))
                if len(ous.filtered(lambda x: not x.share_ou)) > 1:
                    raise ValidationError(
                            'You cannot reconcile entries from different Operation Units.'
                        )
                
        return super().reconcile()
