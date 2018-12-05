{
    'name': "Custom App Store",
    'version': "1.0.8",
    'author': "Sythil Tech",
    'category': "Tools",
    'support': "steven@sythiltech.com.au",
    'summary': "Create your own app store",
    'license':'LGPL-3',
    'data': [
        'views/module_overview_templates.xml',
        'views/module_overview_views.xml',
        'views/appstore_account_views.xml',
        'views/menus.xml',
        'data/website.menu.csv',
        'data/ir.cron.csv',
        'security/ir.model.access.csv',
    ],
    'demo': [],
    'depends': ['website'],
    'images':[
        'static/description/1.jpg',
    ],
    'installable': True,
}