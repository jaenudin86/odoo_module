from odoo import models, fields, api
import logging
import json

_logger = logging.getLogger(__name__)

class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    product_properties_dict = fields.Text(
        string="Product Properties Dict",
        compute="_compute_product_properties_dict",
        store=False
    )

    @api.depends('product_id', 'product_id.categ_id')
    def _compute_product_properties_dict(self):
        for line in self:
            properties = {}

            if line.product_id and line.product_id.categ_id:
                category = line.product_id.categ_id

                # Ambil definisi properti dari kategori (list of dicts)
                prop_def_list = category.product_properties_definition or []

                # Log untuk cek struktur prop_def_list
                _logger.info("===== FULL CATEGORY PROPERTY LIST =====")
                _logger.info(prop_def_list)

                # Ambil nilai properti dari produk
                prop_values = line.product_id.product_properties

                # 🔹 Pastikan `prop_values` dalam bentuk dictionary
                if isinstance(prop_values, str):
                    try:
                        prop_values = json.loads(prop_values)
                    except json.JSONDecodeError:
                        _logger.error("JSON Decode Error: %s", prop_values)
                        prop_values = {}

                if not isinstance(prop_values, dict):
                    _logger.error("Invalid prop_values format: %s", prop_values)
                    prop_values = {}

                # 🔹 Konversi list ke dictionary dengan key hash yang benar
                prop_def_dict = {
                    prop.get("id") or prop.get("name") or prop.get("code") or "UNKNOWN": prop.get("string") 
                    for prop in prop_def_list if isinstance(prop, dict)
                }

                _logger.info("===== PROPERTY DEFINITION (CATEGORY) =====")
                _logger.info(prop_def_dict)

                _logger.info("===== PROPERTY VALUES (PRODUCT) =====")
                _logger.info(prop_values)

                # 🔹 Loop berdasarkan key hash dari kategori
                for key_hash, label in prop_def_dict.items():
                    if key_hash == "UNKNOWN":
                        _logger.warning("⚠️ WARNING: Ada kategori tanpa ID yang valid!")

                    value = prop_values.get(key_hash)  # Ambil berdasarkan hash key

                    # 🔹 Perbaikan utama: Jangan ubah nilai valid menjadi "-"
                    if value is None or value == "":
                        value = "-"

                    # 🔹 Jika value adalah Boolean, ubah ke format "Yes"/"No"
                    elif isinstance(value, bool):
                        value = "Yes" if value else "No"

                    # 🔹 Bersihkan string agar tidak ada spasi di awal/akhir
                    elif isinstance(value, str):
                        value = value.strip()

                    # 🔹 Simpan hasil ke dictionary yang sesuai
                    properties[label] = value

                _logger.info("===== FINAL PROPERTIES =====")
                _logger.info(properties)

            # 🔹 Simpan sebagai JSON agar aman di QWeb
            line.product_properties_dict = json.dumps(properties, ensure_ascii=False)
