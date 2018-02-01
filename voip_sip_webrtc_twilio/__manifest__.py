# -*- coding: utf-8 -*-
{
    'name': "Voip Communication - Twilio",
    'version': "1.0.3",
    'author': "Sythil Tech",
    'category': "Tools",
    'support': "steven@sythiltech.com.au",
    'summary': "Add support for Twilio XML",
    'license':'LGPL-3',
    'data': [
        'views/voip_twilio_views.xml',
        'views/voip_call_views.xml',
        'views/voip_twilio_invoice_views.xml',
    ],
    'demo': [],
    'depends': ['voip_sip_webrtc', 'account'],
    'images':[
    ],
    'installable': True,
}