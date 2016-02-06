{
    'name': "SAAS Multi Database (Beta)",
    'version': "1.0",
    'author': "Sythil",
    'category': "Tools",
    'summary':'Let public users create new Odoo databases in your Instance',
    'license':'LGPL-3',
    'data': [
        'views/saas_multi_db_templates.xml',
        'views/saas_database_views.xml',
        'data/website.menu.csv',
        'security/ir.model.access.csv',
    ],
    'demo': [],
    'images':[
        'static/description/2.jpg',
        'static/description/1.jpg',
    ],
    'depends': ['website'],
    'installable': True,
}