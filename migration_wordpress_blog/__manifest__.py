# -*- coding: utf-8 -*-
{
    'name': "Wordpress Migration - Blog Posts",
    'version': "1.0.0",
    'author': "Sythil Tech",
    'category': "Tools",
    'summary': "Copies Wordpress blog posts and comments into Odoo",
    'description': "Copies Wordpress blog posts and comments into Odoo",
    'license':'LGPL-3',
    'data': [
        'views/migration_import_wordpress_views.xml',
    ],
    'demo': [],
    'depends': ['migration_wordpress', 'website_blog'],
    'images':[
        'static/description/1.jpg',
    ],
    'installable': True,
}