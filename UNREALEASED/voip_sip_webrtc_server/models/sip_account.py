# -*- coding: utf-8 -*-
from openerp.http import request
import socket
import threading
import logging
_logger = logging.getLogger(__name__)
import json
import random
import openerp
import odoo
from random import randint
import time
import string
import socket
import re
import hashlib
from odoo import api, fields, models, registry
from odoo.exceptions import UserError, ValidationError
from openerp import SUPERUSER_ID, tools

class SIPAccount(models.Model):

    _name = "sip.account"
    _description = "SIP Account"

    database = fields.Char(string="Database")
    address = fields.Char(string="SIP Address")
    password = fields.Char(string="SIP Password")
    auth_username = fields.Char(string="Auth Username")
    username = fields.Char(string="Username")
    domain = fields.Char(string="Domain")
    outbound_proxy = fields.Char(string="Outbound Proxy")