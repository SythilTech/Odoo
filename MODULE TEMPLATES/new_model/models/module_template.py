# -*- coding: utf-8 -*-
from openerp import api, fields, models

class ModuleTemplate(models.Model):

    _name = "module.template"
    
    example_field = fields.Integer(string="Example Field")
