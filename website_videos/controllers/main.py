# -*- coding: utf-8 -*-

import base64
import werkzeug
import logging
_logger = logging.getLogger(__name__)

import odoo.http as http
from odoo.addons.http_routing.models.ir_http import slug
from odoo.http import request

class WebsiteVideosController(http.Controller):

    @http.route('/videos', type="http", auth="public", website=True)
    def videos(self):
        """Home Page"""
        return request.render('website_videos.home_page', {})

    @http.route('/videos/upload', type="http", auth="user", website=True)
    def videos_upload(self):
        """Video Upload"""
        return request.render('website_videos.upload', {})

    @http.route('/videos/upload/process', type="http", auth="user")
    def videos_upload_process(self, **kwargs):
        create_dict = {}
        create_dict['name'] = kwargs['name']
        create_dict['uploader_id'] = request.env.user.id
        for c_file in request.httprequest.files.getlist('file'):
            create_dict['data'] = base64.b64encode( c_file.read() )
        video = request.env['video.video'].create(create_dict)
        return werkzeug.utils.redirect("/videos/video/" + slug(video))

    @http.route('/videos/stream/<video>.mp4', type="http", auth="public")
    def videos_stream(self, video):
        """Video Stream"""
        video_media = request.env['video.video'].browse(int(video)).data
        headers = [
            ('Content-Type', 'video/mp4'),
        ]

        return werkzeug.wrappers.Response(base64.b64decode(video_media), headers=headers, direct_passthrough=True)

    @http.route('/videos/search', type="http", auth="public", website=True)
    def videos_search(self, **kwargs):
        """Video Search"""

        if 'query' not in kwargs:
            return werkzeug.utils.redirect("/videos")

        videos = request.env['video.video'].search([('name','=ilike',"%" + kwargs['query'] + "%")])

        return request.render('website_videos.search', {'videos': videos})

    @http.route('/videos/video/<model("video.video"):video>', type='http', auth="public", website=True)
    def videos_video(self, video):
        video.view_count += 1
        request.env['video.video.view'].create({'video_id': video.id})
        return request.render('website_videos.video', {'video': video})