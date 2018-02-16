# -*- coding: utf-8 -*-
{
    'name': "Voip Communication - XMPP (Jabber) Extension",
    'version': "1.0.1",
    'author': "Sythil Tech",
    'category': "Tools",
    'support': "steven@sythiltech.com.au",
    'summary': "Extends thae main voip module to allow XMPP (Jabber) messenging",
    'license':'LGPL-3',
    'data': [
        'views/res_partner_views.xml',
        'views/res_users_views.xml',
        'views/voip_sip_webrtc_xmpp_templates.xml',
        'views/xmpp_account_views.xml',
        'views/voip_message_compose_views.xml',
    ],
    'demo': [],
    'depends': ['voip_sip_webrtc'],
    'qweb': ['static/src/xml/*.xml'],
    'images':[
        'static/description/1.jpg',
    ],
    'installable': True,
}