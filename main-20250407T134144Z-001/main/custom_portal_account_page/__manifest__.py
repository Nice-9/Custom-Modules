# -*- coding: utf-8 -*-
{
    'name': "MyAccount Portal Page Layout",

    'summary': """
        This Module change Portal Account page design with changing profile picture feature.
        """,

  

    'author': "Amel Salah",
    'website': "https://github.com/amelsalah",

    'category': 'portal',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base','portal','website','web','bi_pos_scan_mobile_barcode'],

    # always loaded
    'data': [

        'views/templates.xml',

    ],
    'web.assets_frontend': [
    'https://maxcdn.bootstrapcdn.com/bootstrap/3.4.1/css/bootstrap.min.css',
    'https://ajax.googleapis.com/ajax/libs/jquery/3.7.1/jquery.min.js',
    'https://maxcdn.bootstrapcdn.com/bootstrap/3.4.1/js/bootstrap.min.js'
    ],
     'images': [
        'static/description/screenshot.png',
     
    ],


}
