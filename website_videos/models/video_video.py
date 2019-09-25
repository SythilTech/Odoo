# -*- coding: utf-8 -*

import logging
_logger = logging.getLogger(__name__)

from odoo import api, fields, models

class VideoVideo(models.Model):

    _name = "video.video"

    name = fields.Char(string="Name")
    data = fields.Binary(string="Data")
    uploader_id = fields.Many2one('res.users', string="Uploader")
    view_count = fields.Integer(string="View Count")
    comment_ids = fields.One2many('video.video.comment', 'video_id', string="Comments")

class VideoVideoView(models.Model):

    _name = "video.video.view"

    video_id = fields.Many2one('video.video', string="Video")

class VideoVideoComment(models.Model):

    _name = "video.video.comment"

    video_id = fields.Many2one('video.video', string="Video")
    author_id = fields.Many2one('res.users', string="Author")
    content = fields.Text(string="Content")