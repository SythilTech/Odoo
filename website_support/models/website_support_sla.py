# -*- coding: utf-8 -*-
import datetime

from openerp import api, fields, models

class WebsiteSupportSLA(models.Model):

    _name = "website.support.sla"

    name = fields.Char(string="Name", translate=True)
    description = fields.Text(string="Description", translate=True)
    #business_hours_id = fields.Many2one('resource.calendar', string="Business Hours")
    response_time_ids = fields.One2many('website.support.sla.response', 'vsa_id', string="Category Response Times")

class WebsiteSupportSLAResponse(models.Model):

    _name = "website.support.sla.response"

    vsa_id = fields.Many2one('website.support.sla', string="SLA")
    category_id = fields.Many2one('website.support.ticket.categories', string="Ticket Category")
    response_time = fields.Float(string="Response Time")