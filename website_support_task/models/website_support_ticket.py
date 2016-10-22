# -*- coding: utf-8 -*-
from openerp import api, fields, models

class WebsiteSupportTicketInheritTimesheets(models.Model):

    _inherit = "website.support.ticket"

    task_id = fields.Many2one('project.task', string="Task")

    @api.multi
    def create_task(self):
        self.ensure_one()

        new_task = self.env['project.task'].create({'name': self.subject, 'partner_id': self.partner_id.id, 'description': self.description})
        self.task_id = new_task
