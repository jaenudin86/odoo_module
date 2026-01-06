{
    'name': 'POS Direct Variant Search',
    'version': '18.0.1.0.0',
    'category': 'Point of Sale',
    'summary': 'Show product variants directly in POS search results',
    'description': """
        Show Product Variants Directly in POS Search
        ==============================================
        * Search product variants directly without selecting variant popup
        * Example: Search "Baju Jeans XL" shows XL variant immediately
        * Click to add directly to cart
    """,
    'depends': ['point_of_sale'],
    'data': [
        'views/pos_config_view.xml',
    ],
    'assets': {
        'point_of_sale._assets_pos': [
            'pos_direct_variant/static/src/app/models/pos_store.js',
            'pos_direct_variant/static/src/app/screens/product_screen/product_screen.js',
        ],
    },
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
}