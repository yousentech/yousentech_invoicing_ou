# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from datetime import datetime

class PurchaseOrder(models.Model):
    _inherit = ['purchase.order', 'operation.unit.mixin', 'operation.unit.constraints.mixin']

    operation_unit_id = fields.Many2one(
        'operation.unit',
        readonly=True,
        copy=False
    )

    @api.model
    def create(self, vals):
        if not vals.get('operation_unit_id'):
            vals['operation_unit_id'] = self.env.user.default_ou_id.id
        return super().create(vals)
   
   
    @api.constrains('operation_unit_id')
    def _check_ou_required(self):
        for rec in self:
            if not rec.operation_unit_id:
                raise ValidationError(
                    'Operation Unit is required'
                )
