# -*- coding: utf-8 -*-
{
    'name': "Voip Communication - Transcoding",
    'version': "1.0.1",
    'author': "Sythil Tech",
    'category': "Tools",
    'support': "steven@sythiltech.com.au",
    'summary': "Transcodes audio into formats suitable for RTP transport",
    'license':'LGPL-3',
    'data': [
        'views/voip_call_template_transcode_wizard_views.xml',
        'views/voip_call_template_views.xml',
        'views/voip_account_transcode_wizard_views.xml',
        'views/voip_account_views.xml',
    ],
    'demo': [],
    'depends': ['voip_sip_webrtc'],
    'images':[
    ],
    'installable': True,
}