# -*- coding: utf-8 -*-
from openerp import api, fields, models

class WebsiteSupportTicketInheritProjectTask(models.Model):

    _inherit = "project.task"

    support_ticket_attachment = fields.Binary(string="Attachemnt")
    support_ticket_attachment_filename = fields.Char(string="Attachemnt Filename")