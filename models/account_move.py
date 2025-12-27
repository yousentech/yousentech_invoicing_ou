# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from datetime import datetime

class xx_account_move(models.Model):
    _inherit = 'account.move'
    
    zatca_production_flag = fields.Boolean(compute="_get_zatca_production_value")
    
    def _get_zatca_production_value(self):
        for rec in self:
            zatca_config = self.env['res.config.settings'].search([])
            # print("zatca_config",zatca_config.l10n_sa_api_mode)
            if zatca_config.l10n_sa_api_mode:
               rec.zatca_production_flag = True
            else:
                rec.zatca_production_flag = False
    
    def button_draft(self):
        for rec in self:
            if not self.user_has_groups("qimamhd_zatca_validation.group_exceed_zatca_validation"):

                if rec.type in ('out_invoice','out_refund'):
                    # if rec.edi_state != '':
                        if rec.edi_state in ('sent') :
                            raise ValidationError(
                                "تنبيه : تم الارسال للهيئة لا يمكن اعادة التعيين كمسودة")
            
        return super(xx_account_move,self).button_draft()
    
    def action_reverse(self):
        for rec in self:
            if not self.user_has_groups("qimamhd_zatca_validation.group_exceed_zatca_validation"):
                if rec.type in ('out_refund'):
                    if rec.edi_state in ('sent') :
                        raise ValidationError(
                            "تنبيه : تم الارسال للهيئة لا يمكن اعادة التعيين كمسودة")

        return super(xx_account_move,self).action_reverse()
