{
    'name': "SMS Framework",
    'version': "1.0",
    'author': "Sythil",
    'category': "Tools",
    'summary':'Allows you to send and receive smses from multiple gateways',
    'license':'LGPL-3',
    'data': [
        'views/res_partner.xml',
        'views/ir_actions.xml',
        'views/sms_message.xml',
        'views/sms_template.xml',
        'views/qweb.xml',
        'views/sms_compose.xml',
        'data/ir.cron.csv',
        'res.country.csv',
    ],
    'demo': [],
    'depends': ['web'],
    'images':[
        'static/description/1.jpg',
    ],
    'installable': True,
}