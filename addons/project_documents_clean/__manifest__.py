# -*- coding: utf-8 -*-

{
    'name': 'Project Documents Clean',
    'version': '18.0.1.0.0',
    'category': 'Project',
    'summary': 'Clean project documents module using documents.document',
    'description': """
        A clean implementation of project documents using the documents.document module.
        This module will be built step by step to replace the existing project_documents_extension.
        
        Phase 2: Product Workflow
        - Project document tags using documents.tag
        - Project document lines using documents.document
        - Product workflow with new_workflow service tracking
        - Automatic project creation from sale orders
    """,
    'author': 'Freezooner',
    'website': 'https://www.freezooner.com',
    'depends': [
        'project',
        'documents',
        'product',
        'sale',
        'sale_project',
    ],
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'data/ir_actions.xml',
        'views/task_template_views.xml',
        'views/product_views.xml',
        'views/checkpoint_views.xml',
        # 'views/document_tag_views.xml',  # Temporarily disabled for testing
    ],
    'demo': [
        'demo/demo_data.xml',
    ],
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
} 