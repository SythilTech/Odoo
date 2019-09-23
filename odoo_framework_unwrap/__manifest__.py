{
    'name': "Odoo Framework Unwrap",
    'version': "1.0.0",
    'author': "Sythil Tech",
    'category': "Tools",
    'summary': "Converts an Odoo module into non framework code",
    'license':'LGPL-3',
    'data': [
        'views/module_convert_views.xml',
        'views/menus.xml',
        'data/module.convert.database.csv',
        'data/module.convert.language.csv',
        'data/module.convert.connect.csv',
    ],
    'demo': [],
    'depends': ['web'],
    'external_dependencies' : {
        'python' : ['pyodbc'],
    },
    'images':[
    ],
    'installable': True,
}