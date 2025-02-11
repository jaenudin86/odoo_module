from odoo import models, fields, api
class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    product_properties_definition = fields.Json(
        string="Product Properties Definition",
        compute="_compute_product_properties_definition",
        store=True
    )

    @api.depends('product_id', 'product_id.categ_id')
    def _compute_product_properties_definition(self):
        for line in self:
            if line.product_id and line.product_id.categ_id:
                line.product_properties_definition = line.product_id.categ_id.product_properties_definition
            else:
                line.product_properties_definition = {}
