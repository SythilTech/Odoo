# -*- coding: utf-8 -*-

from openerp import api, fields, models

class MailMassMailingContact(models.Model):

     _inherit = "mail.mass_mailing.contact"

     mobile = fields.Char(string="Mobile") 