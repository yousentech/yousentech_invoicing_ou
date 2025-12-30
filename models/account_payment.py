# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from datetime import datetime

class AccountPayment(models.Model):
    _inherit =  'account.payment' 

    operation_unit_id = fields.Many2one(
        'operation.unit',
     
        copy=False
    )

    @api.model
    def create(self, vals):
        print("vals.get('operation_unit_id'):*******************",vals.get('operation_unit_id'))

        if not vals.get('operation_unit_id'):

            print("vals.get('operation_unit_id'):*******************",vals.get('operation_unit_id'):)
            vals['operation_unit_id'] = self.env.user.default_ou_id.id

        return super().create(vals)


        # payment = super().create(vals)
 
        # if payment.move_id and payment.move_id.operation_unit_id:
        #     payment.operation_unit_id = payment.move_id.operation_unit_id.id
        #     print("vals.get('operation_unit_id'):**********222*********",payment.operation_unit_id)

        
  
        # else:
        #     print("vals.get('operation_unit_id'):**********333*********",payment.operation_unit_id)

        #     payment.operation_unit_id = self.env.user.default_ou_id.id

        # return payment
   
    # @api.constrains('operation_unit_id')
    # def _check_ou_required(self):
    #     for rec in self:
    #         if not rec.operation_unit_id:
    #             raise ValidationError(
    #                 'Operation Unit is required'
    #             )
