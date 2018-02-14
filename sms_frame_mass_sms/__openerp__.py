{
    'name': "SMS Framework - Mass SMS",
    'version': "1.0.3",
    'author': "Sythil Tech",
    'category': "Tools",
    'support': "steven@sythiltech.com.au",
    'summary':'Send out a large volume of smses with unsubscribe built-in',
    'description':'Send out a large volume of smses with unsubscribe built-in',    
    'license':'LGPL-3',
    'data': [
        'views/sms_mass_views.xml',
        'data/res.groups.csv',
        'security/ir.model.access.csv',
        #'data/base_action_rule.xml'
    ],
    'demo': [],
    'depends': ['sms_frame'],
    'images':[
        'static/description/1.jpg',
    ],
    'installable': True,
}