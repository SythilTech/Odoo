# -*- coding: utf-8 -*-
from openerp import api, fields, models
import openerp.http as http
from openerp.http import request

class SaasDatabase(models.Model):

    _name = "saas.database"
    
    name = fields.Char(string="Database Name")
    partner_id = fields.Many2one('res.partner', string="Database Partner")
    login = fields.Char(string="Login")
    password = fields.Char(string="Password")
    
    @api.one
    def login_to_saas_user(self):
        request.session.authenticate(self.name, self.login, self.password)
	        
	return http.local_redirect('/web/')