# -*- coding: utf-8 -*-
# Copyright (C) Softhealer Technologies.

from odoo import api, fields, models
from odoo.exceptions import ValidationError
from odoo.osv import expression
import qrcode
from PIL import Image
import base64
from io import BytesIO
import os
import logging
from odoo.modules.module import get_module_path  # ✅ FIX: import resmi

_logger = logging.getLogger(__name__)


class ShProductProduct(models.Model):
    _inherit = "product.product"

    sh_qr_code = fields.Char(string="QR Code", copy=False)
    sh_qr_code_img = fields.Binary(
        string="QR Code Image", copy=False, compute='_compute_sh_qr_code_2', store=True)
    sh_qr_code_with_logo = fields.Binary(
        string="QR Code with Logo", copy=False, compute='_compute_qr_with_logo', store=True)

    def sh_action_open_label_layout_with_qr(self):
        """Tombol open layout label QR"""
        action = self.env['ir.actions.act_window']._for_xml_id(
            'sh_product_qrcode_generator.sh_action_open_label_layout_with_qr'
        )
        action['context'] = {'default_product_ids': self.ids}
        return action

    @api.constrains('sh_qr_code')
    def _validate_qrcode(self):
        """Pastikan QR Code unik per produk"""
        for product in self:
            if product.sh_qr_code:
                duplicate = self.search([
                    ('id', '!=', product.id),
                    ('sh_qr_code', '=', product.sh_qr_code)
                ], limit=1)
                if duplicate:
                    raise ValidationError("A QR code must be unique!")

    @api.model
    def _name_search(self, name, domain=None, operator='ilike', limit=None, order=None):
        """Cari produk berdasarkan kode QR"""
        result = super()._name_search(name, domain=domain, operator=operator,
                                      limit=limit, order=order)
        if not result:
            domain = expression.AND([domain or [], [('sh_qr_code', '=', name)]])
            result = list(self._search(domain, limit=limit, order=order))
        return result

    @api.model_create_multi
    def create(self, vals_list):
        """Generate QR otomatis saat create jika setting aktif"""
        res = super().create(vals_list)
        is_create_qr_code = self.env['ir.config_parameter'].sudo().get_param(
            'sh_product_qrcode_generator.is_sh_product_qrcode_generator_when_create')
        if is_create_qr_code:
            for product in res:
                product._compute_sh_qr_code_2()
                product._compute_qr_with_logo()
        return res

    @api.depends('sh_qr_code')
    def _compute_sh_qr_code_2(self):
        """Generate QR Code standar (tanpa logo)"""
        for product in self:
            if not product.sh_qr_code:
                product.sh_qr_code_img = False
                continue
            try:
                qr = qrcode.QRCode(
                    version=1,
                    error_correction=qrcode.constants.ERROR_CORRECT_M,
                    box_size=10,
                    border=2,
                )
                qr.add_data(product.sh_qr_code)
                qr.make(fit=True)
                img = qr.make_image(fill_color="black", back_color="white")

                buffer = BytesIO()
                img.save(buffer, format='PNG')
                product.sh_qr_code_img = base64.b64encode(buffer.getvalue())
            except Exception as e:
                _logger.warning(f"⚠️ Failed to generate QR for {product.name}: {e}")
                product.sh_qr_code_img = False

    @api.depends('sh_qr_code')
    def _compute_qr_with_logo(self):
        """Generate QR Code dengan logo di tengah (aman discan)"""
        for product in self:
            if not product.sh_qr_code:
                product.sh_qr_code_with_logo = False
                continue

            try:
                # Buat QR dasar dengan koreksi tinggi (30%)
                qr = qrcode.QRCode(
                    version=1,
                    error_correction=qrcode.constants.ERROR_CORRECT_H,
                    box_size=10,
                    border=2,
                )
                qr.add_data(product.sh_qr_code)
                qr.make(fit=True)
                qr_img = qr.make_image(fill_color="black", back_color="white").convert('RGB')

                # Path logo di modul
                module_path = get_module_path('sh_product_qrcode_generator')
                logo_path = os.path.join(module_path, 'static', 'logopuco.png')
                _logger.info(f"Logo path: {logo_path}")

                if os.path.exists(logo_path):
                    logo = Image.open(logo_path)
                    qr_width, qr_height = qr_img.size

                    # 🔧 Ukuran aman agar tetap bisa discan
                    logo_size = int(qr_width * 0.18)
                    logo.thumbnail((logo_size, logo_size), Image.LANCZOS)

                    # Tambahkan border putih di sekitar logo agar QR tetap terbaca
                    border_size = 6
                    logo_bg_size = logo_size + border_size
                    logo_bg = Image.new('RGB', (logo_bg_size, logo_bg_size), 'white')
                    logo_pos = ((logo_bg_size - logo.size[0]) // 2, (logo_bg_size - logo.size[1]) // 2)
                    logo_bg.paste(logo, logo_pos)

                    # Posisi tempel di tengah QR
                    bg_pos = ((qr_width - logo_bg_size) // 2, (qr_height - logo_bg_size) // 2)
                    qr_img.paste(logo_bg, bg_pos)

                    _logger.info("✅ Logo ditempel di QR dengan ukuran aman")

                else:
                    _logger.warning("⚠️ Logo tidak ditemukan, QR dibuat tanpa logo")

                # Simpan hasil QR ke field binary
                buffer = BytesIO()
                qr_img.save(buffer, format='PNG', quality=95)
                product.sh_qr_code_with_logo = base64.b64encode(buffer.getvalue())

            except Exception as e:
                _logger.warning(f"⚠️ Error generating QR with logo for {product.name}: {e}")
                product.sh_qr_code_with_logo = False
