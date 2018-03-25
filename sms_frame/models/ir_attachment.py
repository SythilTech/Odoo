# -*- coding: utf-8 -*-
from openerp import api, fields, models

class IrAttachmentSMS(models.Model):

    _inherit = "ir.attachment"
    
    mms = fields.Boolean(string="MMS")