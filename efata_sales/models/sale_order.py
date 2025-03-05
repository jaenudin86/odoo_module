from odoo import models, fields, api, exceptions
import logging
import logging
import json

_logger = logging.getLogger(__name__)
from odoo.exceptions import UserError
class InheritSaleOrder(models.Model):
    _inherit = "sale.order"
    _logger = logging.getLogger(__name__)

    state = fields.Selection(selection_add=[('sample_sent', 'Sample Sent')], ondelete={'sample_sent': 'set default'})
    report_type = fields.Selection([
        ('quotation', 'Quotation'),
        ('submission', 'Submission')
    ], string="Report Type", default='quotation')
    # def write(self, vals):
    #     for order in self:
    #         if order.state != 'draft':  # Jika status bukan draft (Quotation)
    #             raise UserError("Anda tidak dapat mengedit Sales Order setelah dikonfirmasi.")
    #     return super(InheritSaleOrder, self).write(vals)
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

    color = fields.Selection([
        ('white', 'White'),
        ('red', 'Red'),
        ('yellow', 'Yellow'),
        ('green', 'Green'),
    ], string="Color", default='white')
    is_new = fields.Boolean(default=True)
    def write(self, vals):  
        # if 'name' in vals and self.name == 'New':
        vals['is_new'] = False
        return super(InheritSaleOrder, self).write(vals)
    color_index = fields.Integer("Color Index", compute="_compute_color_index")

    def _compute_color_index(self):
        """ Mengubah warna pilihan menjadi indeks untuk Odoo tree view """
        color_mapping = {
            'white': 0,
            'red': 1,
            'yellow': 2,
            'green': 3,
        }
        for record in self:
            record.color_index = color_mapping.get(record.color, 0)
        
   
    @api.constrains('order_line')
    def _check_editable(self):
        for order in self:
            _logger.info(f"DEBUG: Order ID: {order.is_new}, Name: {order.name}, State: {order.state}")
            print(f"DEBUG: Order ID: {order.is_new}, Name: {order.name}, State: {order.state}")
            if  order.is_new == True:  # Order belum tersimpan, masih bisa diedit
                continue    
            else:
                raise UserError("You cannot edit the Sales Order after it has been confirmed or if it has a Sales Order number!")
class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'
    tax_amount = fields.Monetary(string="Pajak", compute="_compute_price_with_tax", store=True)

    @api.depends('product_id', 'tax_id', 'price_unit', 'order_id.incl_tax')
    def _compute_price_with_tax(self):
        """Menghitung pajak hanya jika checkbox aktif"""
        for line in self:
            if line.order_id.incl_tax:
                tax_rate = sum(line.tax_id.mapped('amount')) / 100
                line.tax_amount = line.price_unit * tax_rate
            else:
                line.tax_amount = 0.0

# class SaleOrderReport(models.AbstractModel):
#     _name = 'report.sale.report_saleorder'
#     _inherit = 'report.sale.report_saleorder'


    

