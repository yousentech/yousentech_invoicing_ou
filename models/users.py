# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class ResUsers(models.Model):
    _inherit = 'res.users'

    default_ou_id = fields.Many2one(
        'operation.unit',
        string='Default Operation Unit',
        domain="[('id', 'in', allowed_ou_ids)]",
        required=True,
    )

    allowed_ou_ids = fields.Many2many(
        'operation.unit',
        string='Allowed Operation Units',
        required=True,
    )

    @api.constrains('default_ou_id', 'allowed_ou_ids')
    def _check_default_ou(self):
        for rec in self:
            if not rec.default_ou_id:
                raise ValidationError(
                    'Each user must have a Default Operation Unit.'
                )

            if rec.default_ou_id and rec.default_ou_id not in rec.allowed_ou_ids:
                raise ValidationError(
                    'Default OU must be included in Allowed OUs'
                )
  