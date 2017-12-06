# -*- coding: utf-8 -*-
{
    'name': "Voip Communication - Transcription",
    'version': "1.0.0",
    'author': "Sythil Tech",
    'category': "Tools",
    'support': "steven@sythiltech.com.au",
    'summary': "Transcribes SIP calls made through the python automated action",
    'license':'LGPL-3',
    'data': [
        'views/voip_settings_views.xml',
        'views/voip_transcriber_wizard_views.xml',
        'views/voip_call_views.xml',
        'data/voip.transcriber.csv',
        'data/voip_settings.xml',
    ],
    'demo': [],
    'depends': ['voip_sip_webrtc'],
    'external_dependencies': {'python': ['speech_recognition']},    
    'images':[
    ],
    'installable': True,
}