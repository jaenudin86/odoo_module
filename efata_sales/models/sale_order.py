from odoo import models, fields

class SaleOrder(models.Model):
    _inherit = "sale.order"

    state = fields.Selection(selection_add=[('sample_sent', 'Sample Sent')], ondelete={'sample_sent': 'set default'})


def action_send_sample(self):
    self.write({'state': 'sample_sent'})
    for line in self.order_line:
        product = line.product_id
        product.qty_available -= line.product_uom_qty
