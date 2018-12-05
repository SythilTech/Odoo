{
    'name': "Membership Subscription",
    'version': "1.0.0",
    'author': "Sythil Tech",
    'category': "Tools",
    'support': "steven@sythiltech.com.au",
    'summary':'Create membership programs that automatically manage subscriptions using payment tokens',
    'description':'Create membership programs that automatically manage subscriptions using payment tokens',
    'license':'LGPL-3',
    'data': [
        'security/ir.model.access.csv',
        'data/website.menu.csv',
        'views/payment_membership_views.xml',
        'views/membership_subscription_templates.xml',
    ],
    'depends': ['payment_reoccuring'],
    'demo': [
        'demo/ir.module.category.csv',
        'demo/res.groups.xml',
        'demo/payment_membership.xml',
    ],
    'images':[
        'static/description/1.jpg',
    ],
    'installable': True,
}