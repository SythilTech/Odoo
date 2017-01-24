# -*- coding: utf-8 -*
from openerp import api, fields, models

class ResDatingMatching(models.Model):

    _name = "res.dating.matching"
    
    match_name = fields.Char(string="Match Name", help="Function name of extra code to execute during fake profile creation")