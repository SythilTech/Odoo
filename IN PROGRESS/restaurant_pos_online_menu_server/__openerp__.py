{
    'name': "Online Food Takeaway Directory (Alpha)",
    'version': "0.1",
    'author': "Sythil",
    'category': "Point of Sale",
    'summary': "The Takeaway Business Directory",
    'license':'LGPL-3',
    'data': [
        'views/resaurant_pos_online_menu_server_templates.xml',
        'views/pos_category_views.xml',
        'views/takeaway_restaurant_views.xml',
        'data/website.menu.csv',
        'data/takeaway.cuisine.csv',
    ],
    'demo': [],
    'depends': ['point_of_sale','website','base_location_geonames_import'],
    'installable': True,
}