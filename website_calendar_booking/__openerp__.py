{
    'name': "Website Booking Calendar",
    'version': "1.0.3",
    'author': "Vuente",
    'category': "Tools",
    'currency': 'EUR',
    'price': 47.00,
    'summary': "Allow website users to book meetings from the website",
    'license':'LGPL-3',
    'data': [
        'views/website_calendar_views.xml',
        'views/website_calendar_booking_templates.xml',
        'security/ir.model.access.csv',
    ],
    'demo': [],
    'depends': ['website', 'calendar'],
    'images':[
        'static/description/1.jpg',
        'static/description/2.jpg',
        'static/description/3.jpg',
    ],
    'installable': True,
}