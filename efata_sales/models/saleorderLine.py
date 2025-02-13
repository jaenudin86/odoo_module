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

                # Ambil nilai properti dari produk
                prop_values = line.product_id.product_properties

                # Pastikan prop_values berbentuk dictionary, bukan list/string
                if isinstance(prop_values, str):
                    try:
                        prop_values = json.loads(prop_values)
                    except json.JSONDecodeError:
                        prop_values = {}

                if not isinstance(prop_values, dict):
                    prop_values = {}

                # Konversi list ke dictionary dengan key yang benar
                prop_def_dict = {prop.get("name"): prop.get("string") for prop in prop_def_list if isinstance(prop, dict)}

                _logger.info("===== PROPERTY DEFINITION (CATEGORY) =====")
                _logger.info(prop_def_dict)

                _logger.info("===== PROPERTY VALUES (PRODUCT) =====")
                _logger.info(prop_values)

                # Cocokkan ID dari kategori dengan nilai produk
                for key, label in prop_def_dict.items():
                    value = prop_values.get(key, "-")  # Ambil berdasarkan key
                    if isinstance(value, bool):
                        value = "Yes" if value else "No"
                    properties[label] = value

                _logger.info("===== FINAL PROPERTIES =====")
                _logger.info(properties)

            # Simpan sebagai JSON agar tidak error di QWeb
            line.product_properties_dict = json.dumps(properties, ensure_ascii=False)
