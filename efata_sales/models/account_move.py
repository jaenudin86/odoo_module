from odoo import models, fields, api

class AccountMoveInherit(models.Model):
    _inherit = 'account.move'

    def _default_company(self):
        return self.env['res.company'].search([], limit=1).id

    company_id = fields.Many2one('res.company', default=_default_company)
    inter_company_sync = fields.Boolean(string="Sync Transactions", default=True)
    def write(self, vals):
        if 'company_id' in vals and self.env.user.has_group('base.group_multi_company'):
            vals['company_id'] = self.env['res.company'].search([], limit=1).id
        return super(AccountMoveInherit, self).write(vals)
    @api.model
    def create(self, vals):
        move = super(AccountMoveInherit, self).create(vals)
        if move.inter_company_sync:
            other_company = self.env['res.company'].search([('id', '!=', move.company_id.id)], limit=1)
            if other_company:
                move.copy({'company_id': other_company.id})
        return move
class StockPickingInherit(models.Model):
    _inherit = 'stock.picking'

    company_shared = fields.Boolean(string="Share Stock", default=True)

    def action_validate(self):
        if self.company_shared:
            related_pickings = self.env['stock.picking'].search([
                ('company_id', '!=', self.company_id.id),
                ('state', 'in', ['draft', 'waiting'])
            ])
            for pick in related_pickings:
                pick.state = 'done'
        return super(StockPickingInherit, self).action_validate()
