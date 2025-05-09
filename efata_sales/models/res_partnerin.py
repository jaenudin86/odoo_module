from odoo import models, fields,api
from odoo.osv import expression 
import logging

_logger = logging.getLogger(__name__)
class ResPartner(models.Model):
    _inherit = 'res.partner'

    users_visible = fields.Many2one('res.users', string='User')
    users_visible_ids = fields.Many2many(
        'res.users', 
        'res_partner_users_rel',  # nama tabel relasi
        'partner_id', 
        'user_id', 
        string='Visible Users'
    )

