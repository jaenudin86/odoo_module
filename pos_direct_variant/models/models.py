# -*- coding: utf-8 -*-

# from odoo import models, fields, api


# class pos_direct_variant(models.Model):
#     _name = 'pos_direct_variant.pos_direct_variant'
#     _description = 'pos_direct_variant.pos_direct_variant'

#     name = fields.Char()
#     value = fields.Integer()
#     value2 = fields.Float(compute="_value_pc", store=True)
#     description = fields.Text()
#
#     @api.depends('value')
#     def _value_pc(self):
#         for record in self:
#             record.value2 = float(record.value) / 100

