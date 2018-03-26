# -*- coding: utf-8 -*-
{
    'name': "Voip Communication - Twilio Bill",
    'version': "1.0",
    'author': "Sythil Tech",
    'category': "Tools",
    'support': "steven@sythiltech.com.au",
    'summary': "Add support for Twilio XML",
    'license':'LGPL-3',
    'data': [
        'views/voip_call_views.xml',
        'views/voip_twilio_invoice_views.xml',
        'views/voip_twilio_views.xml',
        'views/res_partner_views.xml',
        'views/voip_sip_webrtc_twilio_bill_templates.xml',
        'security/ir.model.access.csv',
    ],
    'demo': [],
    'depends': ['crm','account'],
    'images':[
    ],
    'installable': True,
}