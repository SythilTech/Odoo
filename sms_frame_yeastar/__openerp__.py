{
    'name': "SMS Framework - Yeastar TG 100",
    'version': "1.1.4",
    'author': "Sythil Tech",
    'category': "Tools",
    'support': "steven@sythiltech.com.au",
    'summary':'Allows you to send smses using the Yeastar TG 100 gateway',
    'description':'Allows you to send smses using the Yeastar TG 100 gateway',    
    'license':'LGPL-3',
    'data': [
        'data/sms.gateway.csv',
        'views/sms_account_views.xml',
        'views/ir_actions_todo.xml',
    ],
    'demo': [],
    'depends': ['sms_frame'],
    'images':[
        'static/description/3.jpg',
    ],
    'installable': True,
}