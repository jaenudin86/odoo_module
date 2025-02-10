from odoo import models, fields, api

class ProductTemplate(models.Model):
    _inherit = "product.template"

    # @api.depends('list_price')
    # def _compute_standard_price(self):
    #     for product in self:
    #         if product.list_price:
    #             product.standard_price = product.list_price * 0.8
    
    @api.depends('standard_price')
    def _compute_list_price(self):
            for product in self:
                    product.list_price = product.standard_price / 0.8
    list_price = fields.Float(compute='_compute_list_price',  readonly=False)