{
    'name': 'TeZz Mobile Theme',
    'version': '17.0.1.0.0',
    'summary': 'Mobile-first responsive theme for TeZz marketplace',
    'author': 'TeZz',
    'category': 'Website/Theme',
    'depends': ['website', 'website_sale', 'odoo_marketplace'],
    'data': [
        'views/assets.xml',
        'views/layout.xml',
        'views/shop.xml',
        'views/product.xml',
    ],
    'assets': {
        'web.assets_frontend': [
            'teezz_theme/static/src/css/teezz_mobile.css',
            'teezz_theme/static/src/js/teezz_mobile.js',
        ],
    },
    'installable': True,
    'auto_install': False,
    'license': 'LGPL-3',
}
