{
    'name': "Website POS Online Menu",
    'version': "1.0",
    'author': "Sythil",
    'category': "Tools",
    'summary': "Instantly generate an online menu from products in the POS",
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
    'depends': ['website', 'pos'],
    'images':[
        'static/description/1.jpg',
    ],
    'installable': True,
}