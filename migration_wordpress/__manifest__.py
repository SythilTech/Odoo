# -*- coding: utf-8 -*-
{
    'name': "Wordpress Migration",
    'version': "1.0.1",
    'author': "Sythil Tech",
    'category': "Tools",
    'support': "steven@sythiltech.com.au",
    'summary': "Copy data (pages, media) from wordpress CMS into Odoo",
    'description': "Copy data (pages, media) from wordpress CMS into Odoo",
    'license':'LGPL-3',
    'data': [
        'data/res.groups.csv',
        'security/ir.model.access.csv',
        'views/migration_import_wordpress_views.xml',
        'views/menus.xml',
    ],
    'demo': [],
    'depends': ['website'],
    'images':[
        'static/description/1.jpg',
    ],
    'installable': True,
}