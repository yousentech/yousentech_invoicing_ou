# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from datetime import datetime

class AccountPayment(models.Model):
    _inherit =  'account.payment' 

    operation_unit_id = fields.Many2one(
        'operation.unit',
        default=lambda self: self._default_ou(),
        copy=False   )
    
    def _default_ou(self):
        return self.env.user.ou_config_ids.filtered(lambda x: x.company_id.id == self.company_id.id).default_ou_id.id

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
            vals['operation_unit_id'] = self.env.user.ou_config_ids.filtered(lambda x: x.company_id.id == vals.get('company_id')).default_ou_id.id
           
        return super().create(vals)
 
   
   
    @api.constrains('operation_unit_id')
    def _check_ou_required(self):
        for rec in self:
            if not rec.operation_unit_id:
                raise ValidationError(
                    'Operation Unit is required'
                )
