{
    'name': "SMS Framework - Calendar Alarm",
    'version': "1.1",
    'author': "Sythil Tech",
    'category': "Tools",
    'support': "steven@sythiltech.com.au",
    'summary':'Sends a sms reminder before an event',
    'description':'Sends a sms reminder before an event',    
    'license':'LGPL-3',
    'data': [
        'data/sms.template.csv',
        'data/calendar.alarm.csv',
        'views/ir_actions_todo.xml',
    ],
    'demo': [],
    'depends': ['sms_frame','calendar'],
    'images':[
        'static/description/1.jpg',
    ],
    'installable': True,
}