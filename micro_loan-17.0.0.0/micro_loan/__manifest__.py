# -*- coding: utf-8 -*-
################################################################################
#
#    Kolpolok Ltd. (https://www.kolpolok.com)
#    Author: Kaushik Ahmed Apu, Zarin Tasnim, Aqil Mahmud(<https://www.kolpolok.com>)
#
################################################################################
{
    'name': 'MicroFinance Management System | Micro Loan',

    'summary': "This module facilitates the entire loan and deposit process, from application submission to disbursement and collection, ensuring secure user access",

    'description': "Micro Loan",

    'author': "Kolpolok",

    'website': "https://kolpoloktechnologies.com",

    'category': 'Loan',

    'version': '17.0.0.0',

    'depends': ['base'],

    'data': [
        'security/ir.model.access.csv',
        'views/user.xml',
        'views/loan_views.xml',
        'views/custom_user.xml',
        'views/file_information.xml',
        'views/loan_type.xml',
        'views/loan_disbursement.xml',
        'views/loan_collection.xml',
        'views/deposit_installment.xml',
        'views/deposit_collection.xml',
        'views/deposit_handover.xml',

        'views/micro_loan_menus.xml',
    ],
    'images': ['static/description/banner.gif'],
    'license': 'LGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
