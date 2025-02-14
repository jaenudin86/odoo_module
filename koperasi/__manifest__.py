# -*- coding: utf-8 -*-
{
    'name': "Koperasi Simpan Pinjam",

    'summary': """
        Modul untuk koperasi simpan pinjam""",

    'description': """
Modul untuk koperasi simpan pinjam

feature :
    - Tabungan Harian
    - Deposito
    - Kredit dengan bunga Flat/Efektif/Anuitas
    """,

    'author': "Tim Oddo Trijaa",
    'website': "http://www.trijaya.com",

    # Categories can be used to filter modules in modules listing
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base','account'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'views/views.xml',
        'views/templates.xml',
        'views/simpanan_views.xml',
        # 'report/pinjaman_koperasi_report.xml',
        # 'report/pinjaman_report.xml',
        # 'report/simpanan_koperasi_report.xml',
        # 'report/simpanan_report.xml'
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}