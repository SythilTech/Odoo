{
    'name': "SMS Framework - Birthday",
    'version': "1.0.0",
    'author': "Sythil Tech",
    'category': "Tools",
    'support': "steven@sythiltech.com.au",
    'summary':'Send an sms on a contacts birthday',
    'description':'Send an sms on a contacts birthday',    
    'license':'LGPL-3',
    'data': [
        'data/ir.cron.csv',
        'data/sms_template.xml',
        'views/ir_actions_todo.xml',        
        'views/res_partner_views.xml',
    ],
    'demo': [],
    'depends': ['sms_frame'],
    'images':[
        'static/description/1.jpg',
    ],
    'installable': True,
}