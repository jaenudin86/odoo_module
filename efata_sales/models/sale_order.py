from odoo import models, fields, api, exceptions
import logging
class InheritSaleOrder(models.Model):
    _inherit = "sale.order"
    _logger = logging.getLogger(__name__)

    state = fields.Selection(selection_add=[('sample_sent', 'Sample Sent')], ondelete={'sample_sent': 'set default'})
    report_type = fields.Selection([
        ('quotation', 'Quotation'),
        ('submission', 'Submission')
    ], string="Report Type", default='quotation')

    incl_tax = fields.Boolean(string="Incl. Tax", default=False)
    @api.onchange('incl_tax')
    def _compute_incl_tax(self):
        self._logger.info("=== _compute_price_unit EXECUTED ===")
        for order in self:
            for line in order.order_line:
                line._compute_price_with_tax() # Ensure price unit change is handled
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
        
class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'
    tax_amount = fields.Monetary(string="Pajak", compute="_compute_price_with_tax", store=True)

    # @api.depends('product_id', 'tax_id', 'price_unit', 'order_id.incl_tax')
    # def _compute_price_with_tax(self):
    #     """Menghitung pajak hanya jika checkbox aktif"""
    #     for line in self:
    #         if line.order_id.incl_tax:
    #             tax_rate = sum(line.tax_id.mapped('amount')) / 100
    #             line.tax_amount = line.price_unit * tax_rate
    #         else:
    #             line.tax_amount = 0.0