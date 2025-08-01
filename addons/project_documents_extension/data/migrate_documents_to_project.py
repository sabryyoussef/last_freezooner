# -*- coding: utf-8 -*-
"""
Data Migration Script: Move Documents from Task to Project Level
This script safely migrates document data from task level to project level
without breaking existing functionality.
"""

from odoo import api, SUPERUSER_ID


def migrate_documents_to_project_level(env):
    """
    Migrate documents from task level to project level
    This is a safe migration that preserves existing data
    """
    print("Starting document migration to project level...")
    
    # Step 1: Migrate Required Documents from Tasks to Projects
    migrate_required_documents(env)
    
    # Step 2: Migrate Deliverable Documents from Tasks to Projects  
    migrate_deliverable_documents(env)
    
    # Step 3: Update task document references to point to project documents
    update_task_document_references(env)
    
    print("Document migration completed successfully!")


def migrate_required_documents(env):
    """Migrate required documents from tasks to their parent projects"""
    print("Migrating required documents...")
    
    # Get all tasks with required documents
    tasks_with_docs = env['project.task'].search([
        ('document_required_type_ids', '!=', False)
    ])
    
    for task in tasks_with_docs:
        if task.project_id:
            project = task.project_id
            
            # Copy required documents from task to project
            for task_doc in task.document_required_type_ids:
                # Check if document already exists in project
                existing_doc = env['project.document.required.line'].search([
                    ('project_id', '=', project.id),
                    ('document_type_id', '=', task_doc.document_type_id.id),
                    ('issue_date', '=', task_doc.issue_date)
                ])
                
                if not existing_doc:
                    # Create new document in project
                    env['project.document.required.line'].create({
                        'project_id': project.id,
                        'document_type_id': task_doc.document_type_id.id,
                        'document_id': task_doc.document_id.id,
                        'is_required': task_doc.is_required,
                        'expiry_date': task_doc.expiry_date,
                        'reminder_days': task_doc.reminder_days,
                        'is_verify': task_doc.is_verify,
                        'number': task_doc.number,
                        'issue_date': task_doc.issue_date,
                        'attachment_ids': [(6, 0, task_doc.attachment_ids.ids)],
                        'expiration_reminder': task_doc.expiration_reminder,
                        'expiration_reminder_sent': task_doc.expiration_reminder_sent,
                        'document_create_date': task_doc.document_create_date,
                    })
    
    print(f"Migrated required documents for {len(tasks_with_docs)} tasks")


def migrate_deliverable_documents(env):
    """Migrate deliverable documents from tasks to their parent projects"""
    print("Migrating deliverable documents...")
    
    # Get all tasks with deliverable documents
    tasks_with_docs = env['project.task'].search([
        ('document_type_ids', '!=', False)
    ])
    
    for task in tasks_with_docs:
        if task.project_id:
            project = task.project_id
            
            # Copy deliverable documents from task to project
            for task_doc in task.document_type_ids:
                # Check if document already exists in project
                existing_doc = env['project.document.type.line'].search([
                    ('project_id', '=', project.id),
                    ('document_type_id', '=', task_doc.document_type_id.id),
                    ('issue_date', '=', task_doc.issue_date)
                ])
                
                if not existing_doc:
                    # Create new document in project
                    env['project.document.type.line'].create({
                        'project_id': project.id,
                        'document_type_id': task_doc.document_type_id.id,
                        'document_id': task_doc.document_id.id,
                        'is_required': task_doc.is_required,
                        'expiry_date': task_doc.expiry_date,
                        'reminder_days': task_doc.reminder_days,
                        'is_verify': task_doc.is_verify,
                        'number': task_doc.number,
                        'issue_date': task_doc.issue_date,
                        'attachment_ids': [(6, 0, task_doc.attachment_ids.ids)],
                        'expiration_reminder': task_doc.expiration_reminder,
                        'expiration_reminder_sent': task_doc.expiration_reminder_sent,
                        'document_create_date': task_doc.document_create_date,
                    })
    
    print(f"Migrated deliverable documents for {len(tasks_with_docs)} tasks")


def update_task_document_references(env):
    """Update task document references to point to project documents"""
    print("Updating task document references...")
    
    # This function can be used to update task views to show project documents
    # For now, we'll keep both task and project documents for backward compatibility
    pass


def rollback_migration(env):
    """
    Rollback migration if needed
    This removes project-level documents and restores task-level documents
    """
    print("Rolling back document migration...")
    
    # Delete project-level documents
    env['project.document.required.line'].search([]).unlink()
    env['project.document.type.line'].search([]).unlink()
    
    print("Migration rollback completed!")


# Migration execution functions
def execute_migration(cr):
    """Execute the migration"""
    env = api.Environment(cr, SUPERUSER_ID, {})
    migrate_documents_to_project_level(env)


def execute_rollback(cr):
    """Execute the rollback"""
    env = api.Environment(cr, SUPERUSER_ID, {})
    rollback_migration(env)


if __name__ == "__main__":
    # This can be called manually for testing
    pass 