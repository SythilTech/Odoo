# -*- coding: utf-8 -*-
{
    'name': "Website POS Online Menu",
    'version': "1.1.1",
    'author': "Sythil Tech",
    'category': "Point of Sale",
    'support': "steven@sythiltech.com.au",
    'summary': "Keep your website menu in sync with the POS prices and products",
    'license':'LGPL-3',
    'data': [
        'views/website_pos_online_menu_templates.xml',
        'data/website.menu.csv',
    ],
    'demo': [],
    'depends': ['point_of_sale','website'],
    'images':[
        'static/description/1.jpg',
    ],
    'installable': True,
}