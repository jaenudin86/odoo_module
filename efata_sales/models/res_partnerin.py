from odoo import models, fields

class ResPartner(models.Model):
    _inherit = 'res.partner'

    users_visible = fields.Many2one('res.users', string='User')
