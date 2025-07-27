# -*- coding: utf-8 -*-
{
    'name': "Compliance Cycle",
    'summary': """
        Compliance management and workflow for partners
    """,
    'description': """
        This module provides comprehensive compliance management features:
        - Partner compliance tracking
        - Business structure management
        - Shareholder compliance
        - Address management
        - Compliance workflow stages
    """,
    'author': "Your Company",
    'website': "https://www.yourcompany.com",
    'category': 'Compliance',
    'version': '1.0.0',
    'depends': [
        'base',
        'crm',
        'partner_organization',
        'partner_custom_fields',
        'documents',
        'crm_log',
        'project_documents_extension',
    ],
    'data': [
        'security/security.xml',
        'data/data.xml',
        'views/business_structure.xml',
        'views/partner.xml',
        'views/compliance.xml',
        'views/onboarding.xml',
        'security/ir.model.access.csv',
    ],
    'demo': [
        'demo/demo_data.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
} 