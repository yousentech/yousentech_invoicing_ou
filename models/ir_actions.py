# -*- coding: utf-8 -*-
from odoo import models
from odoo.osv import expression
from odoo.tools.safe_eval import safe_eval


class IrActionsActWindow(models.Model):
    _inherit = 'ir.actions.act_window'

    def _you_ou_get_action_domain(self, res_model):
        """Return OU filter for accounting actions.

        This replaces the former ir.rule behavior with an action-level domain only.
        It is intentionally limited to the same models that had rules before:
        account.move and account.payment.
        """
        if res_model not in ('account.move', 'account.payment'):
            return []

        allowed_ou_ids = self.env.user.ou_config_ids.mapped('allowed_ou_ids').ids
        return [
            '|',
            ('operation_unit_id', '=', False),
            ('operation_unit_id', 'in', allowed_ou_ids),
        ]

    def _you_ou_eval_action_domain(self, domain):
        if not domain:
            return []
        if isinstance(domain, (list, tuple)):
            return list(domain)
        try:
            return safe_eval(domain, {
                'context': dict(self.env.context),
                'uid': self.env.uid,
                'user': self.env.user,
                'active_id': self.env.context.get('active_id'),
                'active_ids': self.env.context.get('active_ids'),
                'active_model': self.env.context.get('active_model'),
            })
        except Exception:
            # Do not risk breaking a live customer action if a custom domain contains
            # variables we cannot safely evaluate here.
            return None

    def _you_ou_apply_domain_to_read_result(self, action_data):
        ou_domain = self._you_ou_get_action_domain(action_data.get('res_model'))
        if not ou_domain:
            return action_data

        base_domain = self._you_ou_eval_action_domain(action_data.get('domain'))
        if base_domain is None:
            return action_data

        action_data['domain'] = expression.AND([base_domain, ou_domain])
        return action_data

    def read(self, fields=None, load='_classic_read'):
        result = super().read(fields=fields, load=load)
        if fields and 'domain' not in fields and 'res_model' not in fields:
            return result
        for action_data in result:
            self._you_ou_apply_domain_to_read_result(action_data)
        return result
