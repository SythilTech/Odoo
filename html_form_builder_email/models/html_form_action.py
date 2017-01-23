# -*- coding: utf-8 -*-
from openerp.http import request
import logging
_logger = logging.getLogger(__name__)

from openerp import api, fields, models

class HtmlFormActionEmail(models.Model):

    _inherit = "html.form.action"
    
    from_email = fields.Char(string="From Email", help="When the form is submitted who will this email be from?")
    to_email = fields.Char(string="To Email", help="When the form is submitted who will this email be to?")
    
    @api.onchange('from_email','to_email')
    def _onchange_settings_description_email(self):
        if self.from_email and self.to_email:
            self.settings_description = "From Email: " + self.from_email + ", To Email: " + self.to_email
