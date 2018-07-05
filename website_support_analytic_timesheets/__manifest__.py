{
    'name': "Website Help Desk / Support Ticket - Analytic Timesheets",
    'version': "1.0.4",
    'author': "Sythil Tech",
    'category': "Tools",
    'support': "steven@sythiltech.com.au",
    'summary':'Track time spend on tickets',
    'license':'LGPL-3',
    'data': [
        'views/website_support_ticket_views.xml',
        'views/website_support_ticket_templates.xml',
        'views/account_analytic_line_views.xml',
        'views/website_support_settings_views.xml',
        'security/ir.rule.csv',
        'data/account.analytic.account.csv',
    ],
    'demo': [],
    'depends': ['website_support','hr_timesheet'],
    'images':[
        'static/description/1.jpg',
    ],
    'installable': True,
}