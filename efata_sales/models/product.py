from odoo import models, fields, api

class ProductTemplate(models.Model):
    _inherit = "product.template"

    # @api.depends('list_price')
    # def _compute_standard_price(self):
    #     for product in self:
    #         if product.list_price:
    #             product.standard_price = product.list_price * 0.8
    reference2 = fields.Char(string="Reference 2")
    @api.depends('standard_price')
    def _compute_list_price(self):
            for product in self:
                    product.list_price = product.standard_price / 0.75
    list_price = fields.Float(compute='_compute_list_price',  readonly=False)


class ProductProduct(models.Model):
        _inherit = "product.template"

        def name_get(self):
                result = []
                for product in self:
                 reference = product.default_code or ""
                name = product.reference2 or ""
                barcode = product.name or ""
                full_name = f"[{reference}] {name} - {barcode}" if name else f"{reference} - {barcode}"
                result.append((product.id, full_name))
                return result

        @api.model
        def name_search(self, name='', args=None, operator='ilike', limit=100):
                args = args or []
                if name:
                        domain = ['|', '|',
                                ('default_code', operator, name),
                                ('reference2', operator, name),
                                ('barcode', operator, name)]
                else:
                        domain = []

                products = self.search(domain + args, limit=limit)
                if not products:
                        return []
                return products.name_get()

