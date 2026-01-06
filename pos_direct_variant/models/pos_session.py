from odoo import models

class PosSession(models.Model):
    _inherit = 'pos.session'
    
    def _load_data_params(self, config):
        params = super()._load_data_params(config)
        # Ensure all product variants are loaded
        if 'product.product' in params:
            params['product.product']['domain'] = [('available_in_pos', '=', True)]
        return params