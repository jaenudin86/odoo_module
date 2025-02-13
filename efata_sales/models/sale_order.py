from odoo import models, fields, api

class InheritSaleOrder(models.Model):
    _inherit = "sale.order"

    state = fields.Selection(selection_add=[('sample_sent', 'Sample Sent')], ondelete={'sample_sent': 'set default'})

    type_transaksi = fields.Selection([
        ('so', 'Sales Order'),
        ('sample', 'Sample Order')
    ], string="Type Transaksi", default='so')

  
    def _update_type_transaksi(self):
        """ Fungsi tambahan untuk memperbarui type_transaksi tanpa mengubah penyimpanan bawaan """
        for order in self.filtered(lambda r: r.state in ['draft', 'sent']):
            
            # print(f"DEBUG: Order {order.id} - State Sebelum: {order.state} - Type: {order.type_transaksi}")
            if order.type_transaksi == 'sample':
                order.state = 'sample_sent'
            else:
                order.state = 'sale'
                order.type_transaksi = 'so'
    def action_confirm(self):
        """Override action_confirm untuk menetapkan type_transaksi ke 'so' dan mengurangi stok"""
        self._update_type_transaksi()  # 🔹 Tambahkan update state sebelum simpan
        return super().action_confirm()

    def action_sample(self):
        """Membuat fungsi action_sample dengan logika yang sama seperti action_confirm,
        tetapi menetapkan type_transaksi ke 'sample' dan mengurangi stok"""
        self._update_type_transaksi()  # 🔹 Tambahkan update state sebelum simpan
        return super().action_confirm()

    def _update_stock(self):
        """Mengurangi stok produk berdasarkan order line"""
        stock_move_obj = self.env['stock.move']
        stock_location = self.env.ref('stock.stock_location_stock')  # Lokasi Stok Default
        customer_location = self.env.ref('stock.stock_location_customers')  # Lokasi Pelanggan
        
        for order in self:
            for line in order.order_line:
                if line.product_id.type == 'product':  # Hanya produk fisik yang dikurangi
                    stock_move_obj.create({
                        'name': f"Stock Move: {order.name}",
                        'product_id': line.product_id.id,
                        'product_uom_qty': line.product_uom_qty,
                        'product_uom': line.product_uom.id,
                        'location_id': stock_location.id,  # Dari Stok Gudang
                        'location_dest_id': customer_location.id,  # Ke Pelanggan
                        'sale_line_id': line.id,
                        'state': 'confirmed',
                    })._action_confirm()  # Konfirmasi perpindahan stok

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