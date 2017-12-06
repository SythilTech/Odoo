# -*- coding: utf-8 -*-
from openerp import api, fields, models

class SaleConfigSettingsConvert(models.Model):

    _name = "sale.config.settings.convert"
    
    lead_field_id = fields.Many2one('ir.model.fields', string="Lead Field", domain="[('model','=', 'crm.lead')]")
    partner_field_id = fields.Many2one('ir.model.fields', string="Partner Field", domain="[('model','=', 'res.partner')]")