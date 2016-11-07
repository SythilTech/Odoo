# -*- coding: utf-8 -*-
{
    'name': "Website Business Directory",
    'version': "1.0",
    'author': "Sythil Tech",
    'category': "Tools",
    'summary': "A directory of local companies",
    'license':'LGPL-3',
    'data': [
        'views/res_partner_views.xml',
        'views/website_business_directory_templates.xml',
        'views/res_partner_directory_department_views.xml',
        'data/website.menu.csv',
        'data/res.groups.csv',
        'security/ir.model.access.csv',
    ],
    'demo': [],
    'depends': ['mail','website'],
    'images':[
        'static/description/1.jpg',
    ],
    'installable': True,
}