from odoo import models, api
from odoo.exceptions import ValidationError

class OperationUnitConstraintsMixin(models.AbstractModel):
    _name = 'operation.unit.constraints.mixin'
    _description = 'Mixin for validating Operation Unit'

    @api.constrains('operation_unit_id', 'company_id')
    def _check_operation_unit_validity(self):
        for record in self:
            ou = getattr(record, 'operation_unit_id', False)
            if not ou:
                raise ValidationError("Operation Unit is required on this document.")

            company = getattr(record, 'company_id', False)
            if company and ou.company_id != company:
                raise ValidationError(
                    "The selected Operation Unit does not belong to the same company as this document."
                )

            user = self.env.user
            if user.allowed_ou_ids and ou not in user.allowed_ou_ids:
                raise ValidationError(
                    "The selected Operation Unit is not allowed for the current user."
                )

