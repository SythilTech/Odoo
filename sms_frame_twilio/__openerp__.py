{
    'name': "SMS Framework - Twilio Gateway",
    'version': "1.0",
    'author': "Sythil",
    'category': "Tools",
    'summary': "Adds Twilio sms gatway to the sms framework",
    'license':'LGPL-3',
    'data': [
        'data/sms.gateway.csv',
        'views/sms_account.xml',
        'views/ir_actions_todo.xml',
        'security/ir.model.access.csv',
    ],
    'demo': [],
    'depends': ['sms_frame'],
    'images':[
    'static/description/1.jpg',
    ],
    'installable': True,
}