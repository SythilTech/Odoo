{
    'name': "Custom App Store Client",
    'version': "1.0.5",
    'author': "Sythil Tech",
    'category': "Tools",
    'support': "steven@sythiltech.com.au",
    'summary': "Let's clients access your custom app store directly from within Odoo",
    'license':'LGPL-3',
    'data': [
        'views/app_store_client_templates.xml',
        'views/module_custom_updates_views.xml',
        'views/ir_module_module_views.xml',
        'data/ir.config_parameter.xml',
    ],
    'qweb': [
        'static/src/xml/app_templates.xml',    
    ],
    'demo': [],
    'depends': ['web'],
    'images':[
    ],
    'installable': True,
}