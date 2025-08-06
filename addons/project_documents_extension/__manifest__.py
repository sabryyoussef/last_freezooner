{
    'name': 'Project Documents Extension',
    'version': '18.0.1.0.0',
    'summary': 'Add deliverable and required documents to projects, inherited from product template',
    'author': 'Sabry Youssef',
    'category': 'Project',
    'depends': [
        'project',
        'documents',
        'product',
        'sale',
        'sale_project',
    ],
    'data': [
        'security/ir.model.access.csv',
        
        # === DOCUMENTS MODULE INTEGRATION VIEWS ===
        # 'views/project_views.xml',  # OLD: Legacy project views - commented out
        'views/x_project_views.xml',  # NEW: X_ project views with documents module integration
        # 'views/product_views.xml',  # OLD: Legacy product views - commented out  
        'views/x_product_views.xml',  # NEW: X_ product views with documents module integration (includes task templates)
        
        # === CONFIGURATION VIEWS (Clean - no legacy refs) ===
        'views/document_type_views.xml',     # Document types & categories
        'views/partner_fields_views.xml',    # Legal entities & hand types
        'views/milestone_views.xml',         # Milestones & checkpoints
        
        # === DATA FILES ===
        'data/reached_checkpoint_data.xml',
        'data/data.xml',
        'data/partner_fields_data.xml',
        'data/milestone_templates.xml',
        'data/test_project_documents.xml',
        'data/demo_sale_order_xdocs.xml',
        'data/cleanup_folders.xml',
        
        # === WIZARD FILES ===
        'wizard/document_upload_wizard.xml',
        'wizard/duplicate_document_warning_wizard.xml',
        'wizard/document_action_confirmation_wizard.xml',
        'wizard/milestone_test_wizard.xml',
        'wizard/quick_milestone_wizard.xml',
        'wizard/select_task_template.xml',
        'views/attachment_views.xml',
    ],
    'post_init_hook': 'post_init_hook',
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
} 