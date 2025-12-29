# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from datetime import datetime
 
class AccountMove(models.Model):
    _inherit ='account.move'

    operation_unit_id = fields.Many2one(
        'operation.unit',
        readonly=True,
        copy=False )

    @api.model
    def create(self, vals):

        if not vals.get('operation_unit_id'):
            vals['operation_unit_id'] = self.env.user.default_ou_id.id

        return super().create(vals)


        # move = super().create(vals)

        # if not move.operation_unit_id:
 
            # sale_lines = move.invoice_line_ids.mapped('sale_line_ids')
            # if sale_lines:
            #     move.operation_unit_id = sale_lines[0].order_id.operation_unit_id.id
            #     return move
 
            # purchase_lines = move.invoice_line_ids.mapped('purchase_line_id')
            # if purchase_lines:
            #     move.operation_unit_id = purchase_lines[0].order_id.operation_unit_id.id
            #     return move
 
        #     move.operation_unit_id = self.env.user.default_ou_id.id

        # return move

        # move = super().create(vals)
        # if not move.operation_unit_id:
        #     ou = move._get_operation_unit_from_source()
        #     if ou:
        #         move.operation_unit_id = ou.id
        # return move
   
    @api.constrains('invoice_line_ids')
    def _check_single_ou(self):
        for move in self:
            ous = move.invoice_line_ids.mapped(
                'sale_line_ids.order_id.operation_unit_id'
            )
            ous |= move.invoice_line_ids.mapped(
                'purchase_line_id.order_id.operation_unit_id'
            )
            ous = ous.filtered(lambda x: x)
            if len(ous) > 1:
                raise ValidationError(
                    'You cannot mix multiple Operation Units in one invoice'
                )
    @api.constrains('operation_unit_id')
    def _check_ou_required(self):
        for rec in self:
            if not rec.operation_unit_id:
                raise ValidationError(
                    'move Operation Unit is required'
                )
 
  
    def _compute_payments_widget_to_reconcile_info(self):
        self.ensure_one()
        result = super()._compute_payments_widget_to_reconcile_info()
        print("_get_outstanding_info_JSON==============")
        # لو ما فيه OU على الفاتورة → نرجع الطبيعي
        if not self.operation_unit_id or not result:
            return result

        ou_id = self.operation_unit_id.id

        # فلترة المدفوعات حسب OU
        filtered_content = []
        for line in result.get('content', []):
            if line.get('operation_unit_id') == ou_id:
                filtered_content.append(line)
        print("_get_outstanding_info_JSON======2========",filtered_content)
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
            if user.allowed_ou_ids and ou not in user.allowed_ou_ids:
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

    def action_register_payment(self):
        res = super().action_register_payment()

        res["context"] = {"default_operation_unit_id": self.operation_unit_id.id}

        return res


class AccountPaymentRegister(models.TransientModel):
    _inherit = "account.payment.register"


    operation_unit_id = fields.Many2one(
        'operation.unit',
        readonly=True,
        copy=False
    )


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line' 

    operation_unit_id = fields.Many2one(
        'operation.unit',
        readonly=True,
        copy=False
    )

    @api.constrains('operation_unit_id')
    def _check_ou_required(self):
        for line in self:
            if not line.operation_unit_id:
                raise ValidationError(
                    'Operation Unit is required on journal items.'
                )
    @api.model
    def create(self, vals):

        if not vals.get('operation_unit_id'):
            if vals.get('move_id'):
                move = self.env['account.move'].browse(vals['move_id'])
                if move.operation_unit_id:
                    vals['operation_unit_id'] = move.operation_unit_id.id

        # if not vals.get('operation_unit_id'):
        #     vals['operation_unit_id'] = self.env.user.default_ou_id.id

        return super().create(vals)
    
    def reconcile(self):
        ous = self.mapped('operation_unit_id').filtered(lambda x: x)
        if len(ous) > 1:
            raise ValidationError(
                'You cannot reconcile entries from different Operation Units.'
            )
        return super().reconcile()
