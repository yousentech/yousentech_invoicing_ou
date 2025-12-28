# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from datetime import datetime
import logging

_logger = logging.getLogger(__name__)

class StockPicking(models.Model):
    _inherit = 'stock.picking'

    operation_unit_id = fields.Many2one(
        'operation.unit',
        readonly=True,
       
        copy=False
    )

    @api.model
    def create(self, vals):
        res = super().create(vals)
        
        if not res.operation_unit_id:
            res.operation_unit_id = self.env.user.default_ou_id.id

        return res


    def button_validate(self):
        for picking in self:
            if not picking.operation_unit_id:
                raise ValidationError(
                    'Operation Unit is required before validating the picking.'
                )

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

        return super().button_validate()
 
class StockMove(models.Model):
    _inherit = 'stock.move' 


    def _get_new_picking_values(self):
        vals = super()._get_new_picking_values()

        # من أمر البيع
        if self.sale_line_id and self.sale_line_id.order_id.operation_unit_id:
            vals['operation_unit_id'] = self.sale_line_id.order_id.operation_unit_id.id
            _logger.warning(
                "OU FROM SALE ORDER %s → %s",
                self.sale_line_id.order_id.name,
                vals['operation_unit_id']
            )
            return vals

        # من أمر الشراء
        if self.purchase_line_id and self.purchase_line_id.order_id.operation_unit_id:
            vals['operation_unit_id'] = self.purchase_line_id.order_id.operation_unit_id.id
            _logger.warning(
                "OU FROM PURCHASE ORDER %s → %s",
                self.purchase_line_id.order_id.name,
                vals['operation_unit_id']
            )
            return vals

        # fallback
        vals['operation_unit_id'] = self.env.user.default_ou_id.id
        _logger.warning(
            "OU FROM USER DEFAULT → %s",
            vals['operation_unit_id']
        )
        return vals

 
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

    def _prepare_account_move_vals(self, acc_valuation,  acc_dest,  journal_id, qty,  description, svl_id,cost ):
        vals = super()._prepare_account_move_vals(
            acc_valuation,
            acc_dest,
            journal_id,
            qty,
            description,
            svl_id,
            cost
        )

        ou = False

        # 1️⃣ من valuation layer
        if self.stock_valuation_layer_ids:
            ou = self.stock_valuation_layer_ids[0].operation_unit_id

        # 2️⃣ من picking
        if not ou and self.picking_id and self.picking_id.operation_unit_id:
            ou = self.picking_id.operation_unit_id

        # 3️⃣ fallback
        if not ou:
            ou = self.env.user.default_ou_id

        if ou:
            vals['operation_unit_id'] = ou.id

        return vals




   
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


