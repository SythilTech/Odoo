{
    'name': "Paypal Credit Card Tokens (BETA)",
    'version': "1.0.1",
    'author': "Sythil Tech",
    'category': "Tools",
    'summary': "Generate a credit card token using paypal vault and make payments using the vaulted card",
    'license':'LGPL-3',
    'data': [    
        'views/payment_acquirer_views.xml',
        'views/payment_method_token_wizard_views.xml',
        'views/res_partner_views.xml',
        'views/payment_payment_token_charge_views.xml',
        'views/account_invoice_views.xml',
    ],
    'demo': [],
    'depends': ['payment_paypal'],
    'images':[
        'static/description/1.jpg',
    ],
    'installable': True,
}