from odoo import models, fields,api

class inheritSaleOrder(models.Model):
    _inherit = "sale.order"

    state = fields.Selection(selection_add=[('sample_sent', 'Sample Sent')], ondelete={'sample_sent': 'set default'})


    type_transaksi = fields.Selection([
        ('so', 'Sales Order'),
        ('sample', 'Sample Order')
    ], string="Type Transaksi", default='so')

    def action_confirm(self):
        """Override action_confirm untuk menetapkan type_transaksi ke 'so'"""
        self.write({'type_transaksi': 'so'})
        return super(inheritSaleOrder, self).action_confirm()

    def action_sample(self):
        """Membuat fungsi action_sample dengan logika yang sama seperti action_confirm,
        tetapi menetapkan type_transaksi ke 'sample'"""
        self.write({'type_transaksi': 'sample'})
        return super(inheritSaleOrder, self).action_confirm()
def action_send_sample(self):
        for order in self:
            # Ubah status ke "Sample Sent"
            order.write({'state': 'sample_sent'})

            # Kurangi stok produk di Inventory
            for line in order.order_line:
                product = line.product_id
                if product.type == 'product':  # Pastikan produk adalah tipe stokable
                    # Cari quant (stok) di lokasi internal
                    quant = self.env['stock.quant'].search([
                        ('product_id', '=', product.id),
                        ('location_id.usage', '=', 'internal')
                    ], limit=1)
                    if quant:
                        # Kurangi quantity on hand
                        quant.write({'quantity': quant.quantity - line.product_uom_qty})
                    else:
                        # Jika quant tidak ditemukan, buat quant baru
                        self.env['stock.quant'].create({
                            'product_id': product.id,
                            'location_id': self.env.ref('stock.stock_location_stock').id,
                            'quantity': -line.product_uom_qty,
                        })
