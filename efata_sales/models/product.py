from odoo import models, fields, api

class ProductTemplate(models.Model):
    _inherit = "product.template"

    @api.onchange('list_price')
    def _onchange_list_price(self):
        """ Mengubah Cost secara otomatis saat Sales Price diubah """
        for product in self:
            if product.list_price:
                product.standard_price = product.list_price * 0.8
