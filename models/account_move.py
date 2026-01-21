# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from datetime import datetime
 
class AccountMove(models.Model):
    _inherit ='account.move'

    operation_unit_id = fields.Many2one(
        'operation.unit',copy=False )

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
        return super().action_post()

    @api.constrains('operation_unit_id', 'company_id')
    def _check_ou_company(self):
        for rec in self:
            if rec.operation_unit_id and rec.company_id:
                if rec.operation_unit_id.company_id != rec.company_id:
                    raise ValidationError(
                        "Operation Unit must belong to the selected company."
                    )
 
 
    def write(self, vals):
        if 'operation_unit_id' in vals:
            for move in self:
                if move.payment_id:
                    raise ValidationError(
                        "Operation Unit must be changed from the Payment, not from the Journal Entry."
                    )
        return super().write(vals)
 
class AccountPaymentRegister(models.TransientModel):
    _inherit = "account.payment.register"

    operation_unit_id = fields.Many2one(
        'operation.unit',
        string='Operation Unit',
        readonly=True,
        related='line_ids.move_id.operation_unit_id',
        copy=False )

    def _init_payments(self, to_process, edit_mode=False):
        # 🔹 حقن OU في قيم الإنشاء
        for vals in to_process:
            create_vals = vals.get('create_vals', {})

            if self.operation_unit_id:
                create_vals['operation_unit_id'] = self.operation_unit_id.id

        # 🔹 نكمل السلوك الأصلي
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
        ous = self.mapped('operation_unit_id').filtered(lambda x: x)
     
        if len(ous) > 1:
            raise ValidationError(
                'You cannot reconcile entries from different Operation Units.'
            )
        return super().reconcile()
