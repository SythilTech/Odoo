# -*- coding: utf-8 -*-
import socket
import logging
from openerp.exceptions import UserError
_logger = logging.getLogger(__name__)
from openerp.http import request
import re
import hashlib
import random
from openerp import api, fields, models
import threading
from . import sdp
import time
import datetime
import struct
import base64
from random import randint
import queue

class VoipAccountAction(models.Model):

    _name = "voip.account.action"
    _description = "VOIP Account Action"

    voip_dialog_id = fields.Many2one('voip.dialog', string="Voip Dialog")
    name = fields.Char(string="Name")
    start = fields.Boolean(string="Start Action")
    account_id = fields.Many2one('voip.account', string="VOIP Account")
    action_type_id = fields.Many2one('voip.account.action.type', string="Call Action", required="True")
    action_type_internal_name = fields.Char(related="action_type_id.internal_name", string="Action Type Internal Name")
    recorded_media_id = fields.Many2one('voip.media', string="Recorded Message")
    user_id = fields.Many2one('res.users', string="Call User")
    from_transition_ids = fields.One2many('voip.account.action.transition', 'action_to_id', string="Source Transitions")
    to_transition_ids = fields.One2many('voip.account.action.transition', 'action_from_id', string="Destination Transitions")

    def _voip_action_initialize_recorded_message(self, voip_call_client):
        _logger.error("Change Action Recorded Message")
        media_data = base64.decodestring(self.recorded_media_id.media)
        return media_data

    def _voip_action_sender_recorded_message(self, media_data, media_index, payload_size):
        rtp_payload_data = media_data[media_index * payload_size : media_index * payload_size + payload_size]
        new_media_index = media_index + 1
        return rtp_payload_data, media_data, new_media_index

class VoipAccountActionTransition(models.Model):

    _name = "voip.account.action.transition"
    _description = "VOIP Call Action Transition"

    name = fields.Char(string="Name")
    trigger = fields.Selection([('dtmf','DTMF Input'), ('auto','Automatic')], default="dtmf", string="Trigger")
    dtmf_input = fields.Selection([('0','0'), ('1','1'), ('2','2'), ('3','3'), ('4','4'), ('5','5'), ('6','6'), ('7','7'), ('8','8'), ('9','9'), ('*','*'), ('#','#')], string="DTMF Input")
    action_from_id = fields.Many2one('voip.account.action', string="From Voip Action")
    action_to_id = fields.Many2one('voip.account.action', string="To Voip Action")

class VoipAccountActionType(models.Model):

    _name = "voip.account.action.type"
    _description = "VOIP Account Action Type"

    name = fields.Char(string="Name")
    internal_name = fields.Char(string="Internal Name", help="function name of code")