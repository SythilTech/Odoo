# -*- coding: utf-8 -*-
{
    'name': "Voip Communication (Alpha)",
    'version': "0.5.3",
    'author': "Sythil Tech",
    'category': "Tools",
    'summary': "Log call times",
    'license':'LGPL-3',
    'data': [
        'views/voip_sip_webrtc_templates.xml',
        'views/res_users_views.xml',
        'views/voip_call_views.xml',
        'views/voip_ringtone_views.xml',
        'security/ir.model.access.csv',
    ],
    'demo': [],
    'depends': ['crm','bus'],
    'qweb': ['static/src/xml/*.xml'],
    'images':[
        'static/description/1.jpg',
    ],
    'installable': True,
}