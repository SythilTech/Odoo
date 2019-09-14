{
    'name': "SMS Framework - Notification",
    'version': "1.0.0",
    'author': "Sythil Tech",
    'category': "Tools",
    'summary':'Allow non technical users access to sms messages',
    'description':'Allow non technical users access to sms messages',
    'license':'LGPL-3',
    'data': [
        'security/ir.model.access.csv',
        'views/sms_message_views.xml',
    ],
    'depends': ['sms_frame'],
    'images':[
        'static/description/1.jpg',
    ],
    'installable': True,
}