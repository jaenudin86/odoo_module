from odoo import models, fields, api
import logging
_logger = logging.getLogger(__name__)

class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    product_properties_dict = fields.Json(
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

                # Ambil definisi properti dari kategori
                prop_def_list = category.product_properties_definition
                # Ambil nilai properti dari produk
                prop_values = line.product_id.product_properties

                # Pastikan prop_values adalah dictionary
                if not isinstance(prop_values, dict):
                    prop_values = {}

                # Ubah list definisi properti menjadi dictionary {key: string}
                prop_def_dict = {prop["name"]: prop["string"] for prop in prop_def_list}

                _logger.info("===== PROPERTY DEFINITION (CATEGORY) =====")
                _logger.info(prop_def_dict)

                _logger.info("===== PROPERTY VALUES (PRODUCT) =====")
                _logger.info(prop_values)

                # Cocokkan data antara product_properties_definition dan product_properties
                for key, label in prop_def_dict.items():
                    value = prop_values.get(key, "-")  # Default "-"
                    properties[label] = value

                _logger.info("===== FINAL PROPERTIES =====")
                _logger.info(properties)

            # Simpan ke field product_properties_dict
            line.product_properties_dict = properties
