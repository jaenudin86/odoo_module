# -*- coding: utf-8 -*-
from odoo import models, fields, api
from io import BytesIO
import base64

try:
    import qrcode
except ImportError:
    qrcode = None


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    sh_qr_code = fields.Char(string="QR Code")
    sh_qr_code_img = fields.Binary(string="QR Code Image", compute='_compute_sh_qr_code_img', store=True)

    @api.depends('sh_qr_code')
    def _compute_sh_qr_code_img(self):
        for record in self:
            record.sh_qr_code_img = False
            if record.sh_qr_code and qrcode:
                qr = qrcode.QRCode(
                    version=1, error_correction=qrcode.constants.ERROR_CORRECT_L,
                    box_size=10, border=4
                )
                qr.add_data(record.sh_qr_code)
                qr.make(fit=True)
                img = qr.make_image()
                bytes_io = BytesIO()
                img.save(bytes_io, format="PNG")
                record.sh_qr_code_img = base64.b64encode(bytes_io.getvalue())

    @api.model_create_multi
    def create(self, vals_list):
        res = super().create(vals_list)
        for rec in res:
            if not rec.sh_qr_code:
                rec.sh_qr_code = f"SO-{rec.name or rec.id}"
        return res
