{
    'name': "PC Backup - Odoo Client",
    'version': "1.0.2",
    'author': "Sythil Tech",
    'category': "Tools",
    'support': "steven@sythiltech.com.au",
    'summary': "Backs up your Odoo databases to your backup server",
    'description': "Backs up your Odoo databases to your backup server",
    'license':'LGPL-3',
    'data': [
        'security/ir.model.access.csv',
        'views/backup_server_views.xml',
        'data/ir.cron.csv'
    ],
    'demo': [],
    'depends': ['web'],
    'images':[
        'static/description/1.jpg',
    ],
    'installable': True,
}