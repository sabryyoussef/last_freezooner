# -*- coding: utf-8 -*-
{
    'name': "Cabinet Directory",
    'author': "Beshoy Wageh",
    'version': '18.0.1.0.0',
    'depends': ['base', 'crm', 'documents', 'hr'],
    'data': [
        'security/ir.model.access.csv',
        'views/views.xml',
        'views/cabinet.xml',
        'views/folder.xml',
        'views/sub_folder_files.xml',
        'wizard/meeting.xml',
        'wizard/handover.xml',
    ],
    'demo': [
        'demo/demo_data.xml',
    ],
    'installable': True,
    'application': False,
}
