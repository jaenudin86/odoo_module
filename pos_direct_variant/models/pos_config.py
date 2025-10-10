from odoo import models, fields, api

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    direct_variant_search = fields.Boolean(
        string='Direct Variant Search',
        config_parameter='pos_direct_variant.direct_variant_search',
        help='Show product variants directly in search results without popup.'
    )
