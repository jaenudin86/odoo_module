from odoo import models, api

class ProductProduct(models.Model):
    _inherit = 'product.product'
    
    @api.model
    def _load_pos_data_fields(self, config_id):
        """Add variant fields for POS"""
        fields = super()._load_pos_data_fields(config_id)
        fields.extend([
            'product_template_attribute_value_ids',
            'product_tmpl_id',
            'combination_indices',
        ])
        return fields