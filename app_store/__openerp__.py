{
    'name': "Custom App Store",
    'version': "0.5.2",
    'author': "Sythil Tech",
    'website':'http://sythiltech.com.au',
    'category': "Tools",
    'summary': "Create your own app store",
    'license':'LGPL-3',
    'data': [
        'views/module_overview_templates.xml',
        'views/module_overview_views.xml',
        'views/appstore_account_views.xml',
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