from odoo import models, api

class OperationUnitMixin(models.AbstractModel):
    _name = 'operation.unit.mixin'
    _description = 'Operation Unit Resolver'

    def _get_operation_unit_from_source(self):
        """تحديد OU حسب الأولويات: Source → Fallback → User"""
        self.ensure_one()
        ou = False

        if hasattr(self, 'operation_unit_id') and self.operation_unit_id:
            ou = self.operation_unit_id
        elif hasattr(self, 'picking_id') and self.picking_id and self.picking_id.operation_unit_id:
            ou = self.picking_id.operation_unit_id
        elif hasattr(self, 'sale_id') and self.sale_id and self.sale_id.operation_unit_id:
            ou = self.sale_id.operation_unit_id
        elif hasattr(self, 'purchase_id') and self.purchase_id and self.purchase_id.operation_unit_id:
            ou = self.purchase_id.operation_unit_id
        elif hasattr(self, 'invoice_line_ids'):
            sale_lines = self.invoice_line_ids.mapped('sale_line_ids')
            if sale_lines:
                ou = sale_lines[0].order_id.operation_unit_id
            purchase_lines = self.invoice_line_ids.mapped('purchase_line_id')
            if purchase_lines:
                ou = purchase_lines[0].order_id.operation_unit_id
        elif hasattr(self, 'stock_valuation_layer_ids') and self.stock_valuation_layer_ids:
            ou = self.stock_valuation_layer_ids[0].operation_unit_id

        if not ou:
            ou = self.env.user.default_ou_id

        return ou
