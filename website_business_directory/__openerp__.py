{
    'name': "Website Business Directory (ALPHA)",
    'version': "0.5",
    'author': "Sythil",
    'category': "Tools",
    'summary': "A directory of local companies",
    'license':'LGPL-3',
    'data': [
        'views/res_partner_views.xml',
        'views/website_business_directory_templates.xml',
        'views/res_partner_directory_department_views.xml',
        'data/website.menu.csv',
        'data/res.groups.csv',
    ],
    'demo': [],
    'depends': ['website'],
    'images':[
        'static/description/1.jpg',
    ],
    'installable': True,
}