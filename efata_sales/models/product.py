from odoo import models, fields, api
import logging
import json
_logger = logging.getLogger(__name__)
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
    combined_name = fields.Char(
        string="Product",
        compute="_compute_combined_name",
        store=True
    )
    show_default_code = fields.Boolean(compute='_compute_show_default_code')

    @api.depends('create_uid')
    def _compute_show_default_code(self):
                for rec in self:
                        is_admin = self.env.user.login == 'Administrator'
                        rec.show_default_code = not is_admin
                        # Debug logs
                _logger.info("===== login =====")
                _logger.info(is_admin, rec.show_default_code,self.env.user.login )
    @api.depends('display_name', 'reference2')
    def _compute_combined_name(self):
        # Cek sekali saja di awal, tidak perlu di-loop
        user = self.env.user
        has_access = user.has_group('sale.sales_user_food_hide_report') or \
                        user.has_group('sale.sales_user_food') or \
                        user.has_group('sale.sales_user_fragrance') or \
                        user.has_group('sale.sales_user_fragrance_hide_report')

        _logger.info("User: %s", user.name)
        _logger.info("Has Access: %s", has_access)

        for record in self:
                if has_access:
                  _logger.info("===== ada akses: %s =====", record.name)
                  if record.reference2:
                        if record.default_code:
                         record.combined_name = f"{record.default_code} {record.reference2} - {record.name}"
                        else:
                         record.combined_name = f"{record.reference2} - {record.name}"
                  else:
                        record.combined_name = record.display_name
                else:
                 _logger.info("===== tidak ada akses: %s =====", record.name)
                if record.reference2:
                        record.combined_name = f"{record.reference2} - {record.name}"
                else:
                        record.combined_name = record.name



class ProductProduct(models.Model):
        _inherit = "product.template"

        def name_get(self):
                result = []
                for product in self:
                 reference = product.default_code or ""
                name = product.reference2 or ""
                barcode = product.name or ""
                if (self.env.user.has_group('base.group_system') or
                self.env.user.has_group('sale.sales_user_food_hide_report') or
                self.env.user.has_group('sale.sales_user_food') or
                self.env.user.has_group('sale.sales_user_fragrance') or
                self.env.user.has_group('sale.sales_user_fragrance_hide_report')):
                        full_name = f"[{reference}] {name} - {barcode}" if name else f"{reference} - {barcode}"
                else:
                        full_name = f"{name} - {barcode}"
                result.append((product.id, full_name))
                return result

        @api.model
        def name_search(self, name='', args=None, operator='ilike', limit=100):
                args = args or []
                if name:
                        name_pattern = f"%{name}%"
                        if (self.env.user.has_group('base.group_system') or
                        self.env.user.has_group('sale.sales_user_food_hide_report') or
                        self.env.user.has_group('sale.sales_user_food') or
                        self.env.user.has_group('sale.sales_user_fragrance') or
                        self.env.user.has_group('sale.sales_user_fragrance_hide_report')):
                                        domain = ['|', '|',
                                                        ('default_code', operator, name_pattern),
                                                        ('reference2', operator, name_pattern),
                                                        ('name', operator, name_pattern)]
                        else:
                                        domain = ['|',
                                                        # ('default_code', operator, name),
                                                        ('reference2', operator, name_pattern),
                                                        ('name', operator, name_pattern)]
                else:
                        domain = []

                products = self.search(domain + args, limit=limit)
                if not products:
                        return []
                return products.name_get()
# class SaleReport(models.Model):
#     _inherit = "sale.   "

#     combined_name = fields.Char(string="Product", readonly=True)

#     def _select(self):
#         select_str = super(SaleReport, self)._select()
#         select_str += ", product_template.combined_name"
#         return select_str

