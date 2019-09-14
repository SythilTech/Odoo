{
    'name': "Website Help Desk / Support Ticket - Billing",
    'version': "1.0.0",
    'author': "Sythil Tech",
    'category': "Tools",
    'summary':'Generate invoices based on amount of time spent on ticket / tasks',
    'license':'LGPL-3',
    'data': [
        'views/res_partner_views.xml',
        'security/ir.model.access.csv',
    ],
    'demo': [],
    'depends': ['website_support','website_support_analytic_timesheets', 'account'],
    'images':[
        'static/description/1.jpg',
    ],
    'installable': True,
}