from odoo import models, fields, api, exceptions

class InheritSaleOrder(models.Model):
    _inherit = "sale.order"

    state = fields.Selection(selection_add=[('sample_sent', 'Sample Sent')], ondelete={'sample_sent': 'set default'})

    type_transaksi = fields.Selection([
        ('so', 'Sales Order'),
        ('sample', 'Sample Order')
    ], string="Type Transaksi", default='so')

    def action_confirm(self):
        """Override action_confirm untuk memastikan perubahan dilakukan setelah konfirmasi"""
        res = super(InheritSaleOrder, self).action_confirm()  # 🔹 Konfirmasi order dulu
        self._update_type_transaksi()  # 🔹 Baru update state setelahnya
        return res

    def action_sample(self):
        """Fungsi untuk konfirmasi sebagai sample"""
        self.ensure_one()  # Pastikan hanya satu order diproses

        if self.state not in ['draft', 'sent']:
            raise exceptions.UserError("Some orders are not in a state requiring confirmation.")

        self.write({'type_transaksi': 'sample'})  # 🔹 Tetapkan sebagai sample dulu
        res = super(InheritSaleOrder, self).action_confirm()  # 🔹 Konfirmasi order
        self._update_type_transaksi()  # 🔹 Baru update state setelah konfirmasi
        return res

    def _update_type_transaksi(self):
        """Perbarui type_transaksi dan state setelah order dikonfirmasi"""
        for order in self.filtered(lambda r: r.state == 'sale'):  # 🔹 Hanya order yang sudah dikonfirmasi
            if order.type_transaksi == 'sample':
                order.write({'state': 'sample_sent'})  # 🔹 Ubah state setelah action_confirm()
