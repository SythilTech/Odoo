# -*- coding: utf-8 -*-
{
    'name': "Voip Communication - Twilio",
    'version': "1.0.6",
    'author': "Sythil Tech",
    'category': "Tools",
    'support': "steven@sythiltech.com.au",
    'summary': "Add support for Twilio XML",
    'license':'LGPL-3',
    'data': [
        'views/voip_number_views.xml',
        'views/voip_twilio_views.xml',
        'views/voip_call_views.xml',
        'views/voip_twilio_invoice_views.xml',
        'views/res_partner_views.xml',
        'views/voip_call_wizard_views.xml',
        'views/voip_account_action_views.xml',
        'views/voip_sip_webrtc_twilio_templates.xml',
        'views/menus.xml',
        #'data/voip.account.action.type.csv',
        'security/ir.model.access.csv',
    ],
    'demo': [],
    'depends': ['voip_sip_webrtc', 'account'],
    'images':[
    ],
    'installable': True,
}