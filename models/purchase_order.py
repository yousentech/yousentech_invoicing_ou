# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from datetime import datetime

class PurchaseOrder(models.Model):
    _inherit = 'purchase.order' 

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
    
    def _prepare_invoice(self):
        invoice_vals = super(PurchaseOrder, self)._prepare_invoice()
        invoice_vals.update({"operation_unit_id": self.operation_unit_id.id or False})
        return invoice_vals


    def _prepare_picking(self):
        vals = super()._prepare_picking()

        if self.operation_unit_id:
            vals['operation_unit_id'] = self.operation_unit_id.id
        else:
            vals['operation_unit_id'] = self.env.user.default_ou_id.id

        return vals