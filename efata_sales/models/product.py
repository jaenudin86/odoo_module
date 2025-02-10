from odoo import models, fields, api

class ProductTemplate(models.Model):
    _inherit = "product.template"

    @api.depends('list_price')
    def _compute_standard_price(self):
        for product in self:
            if product.list_price:
                product.standard_price = product.list_price * 0.8

    # standard_price = fields.Float(compute='_compute_standard_price', store=True, string='Cost')