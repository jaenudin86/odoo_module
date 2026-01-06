# -*- coding: utf-8 -*-
# Copyright (C) Softhealer Technologies.

from odoo import models, fields, api
from odoo.exceptions import ValidationError
from odoo.osv import expression
from odoo.modules.module import get_module_path
import logging
from io import BytesIO
import base64
import os

_logger = logging.getLogger(__name__)

try:
    import qrcode
    from PIL import Image
except ImportError:
    qrcode = None
    Image = None


class ShProductTemplate(models.Model):
    _inherit = "product.template"

    sh_qr_code = fields.Char(
        string="QR Code", related='product_variant_ids.sh_qr_code', readonly=False)
    sh_qr_code_img = fields.Binary(
        string="QR Code Image", readonly=False, compute='_compute_sh_qr_code_1')
    sh_qr_code_with_logo = fields.Binary(
        string="QR Code with Logo", copy=False, compute='_compute_qr_with_logo', store=True)

    def sh_action_open_label_layout_with_qr(self):
        action = self.env['ir.actions.act_window']._for_xml_id(
            'sh_product_qrcode_generator.sh_action_open_label_layout_with_qr')
        action['context'] = {'default_product_tmpl_ids': self.ids}
        return action

    @api.model
    def _name_search(self, name, domain=None, operator='ilike', limit=None, order=None):
        result = super()._name_search(name, domain=domain, operator=operator, limit=limit, order=order)
        if not result:
            if not domain:
                domain = []
            domain = expression.AND([domain, [('sh_qr_code', '=', name)]])
            result = list(self._search(domain, limit=limit, order=order))
        return result

    @api.constrains('sh_qr_code')
    def _validate_qrcode(self):
        for template in self:
            if template.sh_qr_code:
                products = self.env['product.template'].search(
                    [('id', '!=', template.id), ('sh_qr_code', '=', template.sh_qr_code)])
                if products:
                    raise ValidationError("QR code must be unique !")

    def _generate_product_qr_code(self, product, text=None):
        """Generate QR Code & QR Code with Logo"""
        if not product or not qrcode:
            return

        if text is None:
            text = self.env['ir.sequence'].next_by_code('seq.sh_product_qrcode_generator')
        if not text:
            return

        # === QR dasar (pakai versi lebih besar agar tidak terlalu rapat) ===
        qr_code = qrcode.QRCode(
            version=3,
            error_correction=qrcode.constants.ERROR_CORRECT_H,  # HIGH correction (30%)
            box_size=10,
            border=4
        )
        qr_code.add_data(text)
        qr_code.make(fit=True)
        qr_img = qr_code.make_image(fill_color="black", back_color="white").convert("RGB")

        # Simpan QR tanpa logo
        bytes_io = BytesIO()
        qr_img.save(bytes_io, format="PNG")
        qr_code_image = base64.b64encode(bytes_io.getvalue())

        product.sh_qr_code = text
        product.sh_qr_code_img = qr_code_image

        # === QR dengan logo ===
        try:
            module_path = get_module_path('sh_product_qrcode_generator')
            logo_path = os.path.join(module_path, 'static', 'logopuco.png')
            _logger.info(f"Logo path: {logo_path}")

            if not os.path.exists(logo_path):
                _logger.warning("❌ Logo tidak ditemukan di path tersebut.")
                return

            logo = Image.open(logo_path).convert("RGBA")
            qr_width, qr_height = qr_img.size

            # Ukuran logo: kecilkan jadi 12% dari QR
            logo_size = qr_width // 8
            logo = logo.resize((logo_size, logo_size), Image.Resampling.LANCZOS)

            # Tambahkan background putih tebal agar tetap kontras
            border = int(logo_size * 0.4)
            logo_bg_size = logo_size + border
            logo_bg = Image.new("RGBA", (logo_bg_size, logo_bg_size), "white")

            # Tempel logo ke background
            logo_pos = ((logo_bg_size - logo_size) // 2, (logo_bg_size - logo_size) // 2)
            logo_bg.paste(logo, logo_pos, mask=logo)

            # Tempel background logo di tengah QR
            pos = ((qr_width - logo_bg_size) // 2, (qr_height - logo_bg_size) // 2)
            qr_img.paste(logo_bg, pos, mask=logo_bg)

            # Simpan hasil QR dengan logo
            bytes_logo_io = BytesIO()
            qr_img.save(bytes_logo_io, format="PNG")
            qr_with_logo_image = base64.b64encode(bytes_logo_io.getvalue())

            product.sh_qr_code_with_logo = qr_with_logo_image
            _logger.info("✅ QR code dengan logo berhasil dibuat dan dapat discan")

        except Exception as e:
            _logger.error(f"⚠️ Gagal generate QR dengan logo: {str(e)}")
            product.sh_qr_code_with_logo = qr_code_image

    @api.model_create_multi
    def create(self, vals_list):
        res = super().create(vals_list)
        is_create_qr_code = self.env['ir.config_parameter'].sudo().get_param(
            'sh_product_qrcode_generator.is_sh_product_qrcode_generator_when_create')
        if is_create_qr_code:
            for template in res:
                self._generate_product_qr_code(template)

        for vals, template in zip(vals_list, res):
            if vals.get("sh_qr_code"):
                template.product_variant_id.sh_qr_code = vals.get("sh_qr_code")
        return res

    @api.depends('sh_qr_code')
    def _compute_sh_qr_code_1(self):
        for template in self:
            template.sh_qr_code_img = False
            if template.sh_qr_code:
                self._generate_product_qr_code(template, text=template.sh_qr_code)

    @api.depends('sh_qr_code')
    def _compute_qr_with_logo(self):
        for template in self:
            if template.sh_qr_code:
                self._generate_product_qr_code(template, text=template.sh_qr_code)
