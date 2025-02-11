from odoo import http
from odoo.http import request

class DebugController(http.Controller):
    @http.route('/debug/product_properties', type='http', auth='user')
    def debug_product_properties(self):
        # Ambil satu order line
        line = request.env['sale.order.line'].search([], limit=2)

        # Debug semua fields dalam order line
        result = {
            "ID": line.id,
            "Product Name": line.product_id.name if line.product_id else "No Product",
            # "Properties Raw": line.product_properties,  # Cek isi langsung
            "Properties Dict": line.product_properties_dict,  # Cek apakah dict kosong
        }
        
        return str(result)
