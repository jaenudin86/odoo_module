from odoo import models, fields,api
from odoo.osv import expression 
import logging

_logger = logging.getLogger(__name__)
class ResPartner(models.Model):
    _inherit = 'res.partner'

    users_visible = fields.Many2one('res.users', string='User')

@api.model
def search(self, domain, offset=0, limit=None, order=None):
    domain = domain or []  # pastikan bukan None/False

    _logger.info("Original domain: %s", domain)

    if not self.env.user.has_group('base.group_system'):
        extra_domain = [
            '&',
                ('is_company', '=', True),
                '|',
                    ('users_visible', '=', self.env.user.id),
                    ('users_visible', '=', False)
        ]
        domain += extra_domain

    _logger.info("Modified domain: %s", domain)
    return super().search(domain, offset=offset, limit=limit, order=order)
