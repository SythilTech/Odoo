# -*- coding: utf-8 -*-
import logging
_logger = logging.getLogger(__name__)

from openerp import api, fields, models

class ProjectTaskCloudTasks(models.Model):

    _inherit = "project.task"
    
    cloud_task = fields.Boolean(string="Cloud Task")
    cloud_task_category = fields.Many2one('project.task.cloud.category', string="Cloud Task Category")