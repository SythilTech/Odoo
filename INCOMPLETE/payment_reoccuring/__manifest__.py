{
    'name': "Payment Reoccuring",
    'version': "1.0.0",
    'author': "Sythil Tech",
    'category': "Tools",
    'support': "steven@sythiltech.com.au",
    'summary':'Charge a customer on a reoccuring basis using payment tokens',
    'description':'Charge a customer on a reoccuring basis using payment tokens',
    'license':'LGPL-3',
    'data': [
        'security/ir.model.access.csv',
        'views/payment_subscription_views.xml',
    ],
    'depends': ['website_sale', 'account_invoicing'],
    'images':[
        'static/description/1.jpg',
    ],
    'installable': True,
}