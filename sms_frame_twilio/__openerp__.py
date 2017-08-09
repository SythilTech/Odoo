{
    'name': "SMS Framework - Twilio Gateway",
    'version': "1.1.3",
    'author': "Sythil Tech",
    'category': "Tools",
    'support': "steven@sythiltech.com.au",
    'summary': "Adds Twilio sms gatway to the sms framework",
    'license':'LGPL-3',
    'data': [
        'data/sms.gateway.csv',
        'views/sms_account.xml',
        'views/ir_actions_todo.xml',
        'views/sms_message.xml',
        'security/ir.model.access.csv',
    ],
    'demo': [],
    'depends': ['sms_frame','mail'],
    'images':[
        'static/description/3.jpg',
        'static/description/1.jpg',
        'static/description/2.jpg',
    ],
    'installable': True,
}