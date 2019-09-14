{
    'name': "Website Help Desk / Support Ticket - Create Task",
    'version': "1.1",
    'author': "Sythil Tech",
    'category': "Tools",
    'summary':'Create a task from a support ticket',
    'license':'LGPL-3',
    'data': [
        'views/website_support_ticket_views.xml',
        'views/project_task_views.xml',
    ],
    'demo': [],
    'depends': ['website_support','project'],
    'images':[
        'static/description/1.jpg',
    ],
    'installable': True,
}