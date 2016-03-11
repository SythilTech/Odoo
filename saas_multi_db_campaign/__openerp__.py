{
    'name': "SAAS Multi Database Campaign",
    'version': "1.0",
    'author': "Vuente",
    'category': "Tools",
    'summary':'Adds a mail campaign which new saas users go on, designed to be used with saas_multi_db',
    'license':'LGPL-3',
    'data': [
        'data/mail_template.xml',
        'data/marketing.campaign.csv',
        'data/marketing.campaign.activity.csv',
        'data/ir.filters.csv',
        'data/marketing.campaign.segment.csv',
    ],
    'demo': [],
    'images':[
        'static/description/1.jpg',
    ],
    'depends': ['marketing_campaign','saas_multi_db'],
    'installable': True,
}