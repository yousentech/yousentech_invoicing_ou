# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class OperationUnit(models.Model):
    _name = 'operation.unit'
    _description = 'Operation Unit'
 
    name = fields.Char(required=True)
    company_id = fields.Many2one(
        'res.company',
        required=True,
        default=lambda self: self.env.company
    )
    share_ou = fields.Boolean(string="OU share",default=False)
    active = fields.Boolean(default=True)
