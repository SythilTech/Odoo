# -*- coding: utf-8 -*-
from openerp import api, fields, models

class VoipDialog(models.Model):

    _name = "voip.dialog"

    name = fields.Char(string="Name")
    call_action_ids = fields.One2many('voip.account.action', 'voip_dialog_id', string="Call Actions")