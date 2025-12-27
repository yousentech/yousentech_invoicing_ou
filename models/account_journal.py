# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from datetime import datetime

class xx_account_journal(models.Model):
    _inherit = 'account.journal'
    
    @api.model
    def create(self, vals_list):
        res = super(xx_account_journal,self).create(vals_list)
        if res.type == 'sale' and not self.user_has_groups('base.group_system'):
            raise ValidationError(
                "تنبيه : لا يمكن انشاء او تعديل  الدفاتر اليومية .. تواصل مع مدير النظام")
        return res
    
    # def write(self,vals):
    #     if self.type == 'sale' and not self.user_has_groups('base.group_system'):
    #         raise ValidationError(
    #             "تنبيه : لا يمكن انشاء او تعديل  الدفاتر اليومية .. تواصل مع مدير النظام")

    #     res = super(xx_account_journal,self).write(vals)
    #     if self.type == 'sale' and not self.user_has_groups('base.group_system'):
         
    #         raise ValidationError(
    #             "تنبيه : لا يمكن انشاء او تعديل  الدفاتر اليومية .. تواصل مع مدير النظام")

    #     return res