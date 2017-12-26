# -*- coding: utf-8 -*-
{
    'name': "Voip Communication - Voice Synthesis",
    'version': "1.0.2",
    'author': "Sythil Tech",
    'category': "Tools",
    'support': "steven@sythiltech.com.au",
    'summary': "Text to speech phone calls with dynamic placeholders",
    'license':'LGPL-3',
    'data': [
        'views/voip_settings_views.xml',
        'views/voip_call_template_views.xml',
        'views/voip_voice_message_views.xml',
        'views/voip_account_action_views.xml',
        'data/voip.voice.csv',
        'data/voip.account.action.type.csv',
        'data/voip_settings.xml',
    ],
    'demo': [],
    'depends': ['voip_sip_webrtc'],
    'images':[
    ],
    'installable': True,
}