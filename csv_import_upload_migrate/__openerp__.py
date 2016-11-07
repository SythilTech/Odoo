{
    'name': "Advanced CSV Importer (Alpha)",
    'version': "0.1.1",
    'author': "Sythil Tech",
    'category': "Tools",
    'summary':'Uploads CSV files',
    'description':'Uploads CSV files',    
    'license':'LGPL-3',
    'data': [
        'views/ir_action_background_views.xml',
        'views/csv_import_upload_migrate_templates.xml',
        'data/ir.cron.csv',
    ],
    'demo': [],
    'depends': [],
    'qweb': [
        'static/src/xml/progress_window.xml',
    ],
    'images':[
        'static/description/1.jpg',
    ],
    'installable': True,
}