# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from datetime import datetime

class StockPicking(models.Model):
    _inherit = 'stock.picking'

    operation_unit_id = fields.Many2one(
        'operation.unit',
        readonly=True,
       
        copy=False
    )

    @api.model
    def create(self, vals):
 
        # if vals.get('sale_id'):
        #     sale = self.env['sale.order'].browse(vals['sale_id'])
        #     vals['operation_unit_id'] = sale.operation_unit_id.id

      
        # elif vals.get('purchase_id'):
        #     po = self.env['purchase.order'].browse(vals['purchase_id'])
        #     vals['operation_unit_id'] = po.operation_unit_id.id

        
        # else:
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

    @api.constrains('operation_unit_id', 'company_id')
    def _check_picking_ou_validity(self):
        for picking in self:
            ou = picking.operation_unit_id
            user = self.env.user

            if not ou:
                raise ValidationError("Operation Unit is required on this document.")

            if ou.company_id != picking.company_id:
                raise ValidationError(
                    "The selected Operation Unit does not belong to the same company as this document."
                )

            if user.allowed_ou_ids and ou not in user.allowed_ou_ids:
                raise ValidationError(
                    "The selected Operation Unit is not allowed for the current user."
                )

class StockMove(models.Model):
    _inherit = 'stock.move' 

 
    def _prepare_account_move_vals(self):
        vals = super()._prepare_account_move_vals()

        ou = False
 
        if self.stock_valuation_layer_ids:
            ou = self.stock_valuation_layer_ids[0].operation_unit_id
 
        if not ou and self.picking_id and self.picking_id.operation_unit_id:
            ou = self.picking_id.operation_unit_id
 
        if not ou:
            ou = self.env.user.default_ou_id
 
        if ou:
            vals['operation_unit_id'] = ou.id

        return vals
        # vals = super()._prepare_account_move_vals()
        # ou = self._get_operation_unit_from_source()
        # if ou:
        #     vals['operation_unit_id'] = ou.id
        # return vals



   
    def _prepare_account_move_line(self, qty, cost, credit_account_id, debit_account_id):
        res = super()._prepare_account_move_line(qty, cost, credit_account_id, debit_account_id)
        ou = False

        if self.stock_valuation_layer_ids:
            ou = self.stock_valuation_layer_ids[0].operation_unit_id
        if not ou and self.picking_id and self.picking_id.operation_unit_id:
            ou = self.picking_id.operation_unit_id
        if not ou:
            ou = self.env.user.default_ou_id

        for line in res:
            line[2]['operation_unit_id'] = ou.id if ou else False
        return res

        

    def _prepare_valuation_layer_vals(self):
        vals = super()._prepare_valuation_layer_vals()

        # المصدر الأساسي: picking
        ou = (
            self.picking_id.operation_unit_id
            if self.picking_id and self.picking_id.operation_unit_id
            else self.env.user.default_ou_id
        )

        if ou:
            vals['operation_unit_id'] = ou.id

        return vals



class StockValuationLayer(models.Model):
    _inherit = 'stock.valuation.layer'

    operation_unit_id = fields.Many2one(
        'operation.unit',
        string='Operation Unit',
        readonly=True,
        copy=False
    )


