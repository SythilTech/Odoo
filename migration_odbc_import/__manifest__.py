# -*- coding: utf-8 -*-
{
    'name': "Migration Toolkit",
    'version': "1.4.6",
    'author': "Sythil Tech",
    'category': "Tools",
    'support': "steven@sythiltech.com.au",
    'summary': "A series of tools designed to assist in migration/synchronisation of external data",
    'description': "A series of tools designed to assist in migration/synchronisation of external data",
    'license':'LGPL-3',
    'data': [
        'views/migration_import_odbc_views.xml',
        'views/migration_import_odbc_log_views.xml',
        'views/migration_import_odbc_table_views.xml',
        'views/migration_import_odbc_table_field_views.xml',
        'views/migration_import_odbc_table_field_distinct_views.xml',
        'views/migration_import_odbc_relationship_views.xml',
        'views/menus.xml',
        'views/migration_odbc_import_templates.xml',
        'data/migration.import.odbc.connect.csv',
    ],
    'demo': [],
    'depends': [],
    'external_dependencies' : {
        'python' : ['pyodbc'],
    },
    'qweb': [
        'static/src/xml/widget.xml',
    ],
    'images':[
        'static/description/1.jpg',
    ],
    'installable': True,
}