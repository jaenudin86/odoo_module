

from odoo import models, fields, api 
class InheritPartner(models.Model):    
     _inherit = 'res.partner'
     is_instructor = fields.Boolean('Instructor ?')