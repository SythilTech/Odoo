{
    'name': "Website Dating - Singles Events",
    'version': "1.0",
    'author': "Sythil Tech",
    'category': "Tools",
    'support': "steven@sythiltech.com.au",
    'summary': "Go places with other singles",
    'license':'LGPL-3',
    'data': [
        'views/website_dating_templates.xml',
        'views/menus_views.xml',
        'views/event_event_views.xml',
        'views/res_partner_views.xml',
        'data/website.menu.csv',
        'data/ir.cron.csv',
    ],
    'demo': [],
    'depends': ['website_dating','event'],
    'images':[
        'static/description/1.jpg',
    ],
    'installable': True,
}