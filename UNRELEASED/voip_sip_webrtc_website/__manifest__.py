# -*- coding: utf-8 -*-
{
    'name': "Voip Communication - Website (Click to Dial)",
    'version': "1.0.0",
    'author': "Sythil Tech",
    'category': "Tools",
    'support': "steven@sythiltech.com.au",
    'summary': "Place a button on the website which calls a user in the system",
    'license':'LGPL-3',
    'data': [
        'views/voip_button_views.xml',
        'views/voip_templates.xml',
    ],
    'demo': [],
    'depends': ['voip_sip_webrtc', 'website'],
    'images':[
    ],
    'installable': True,
}