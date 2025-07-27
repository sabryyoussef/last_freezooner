from odoo import api

def copy_documents_from_product_to_project(env, project, product_templates):
    """
    Copy required and deliverable documents from product templates to the given project, avoiding duplicates.
    """
    # Required Documents
    for product_tmpl in product_templates:
        for doc_line in product_tmpl.document_required_type_ids:
            if not project.document_required_type_ids.filtered(lambda l: l.document_id == doc_line.document_id):
                env['project.document.required.line'].sudo().create({
                    'project_id': project.id,
                    'document_id': doc_line.document_id.id,
                    'is_required': doc_line.is_required,
                })
        for doc_line in product_tmpl.document_type_ids:
            if not project.document_type_ids.filtered(lambda l: l.document_id == doc_line.document_id):
                env['project.document.type.line'].sudo().create({
                    'project_id': project.id,
                    'document_id': doc_line.document_id.id,
                    'is_required': doc_line.is_required,
                })

def copy_documents_from_project_to_task(env, task, project):
    """
    Copy required and deliverable documents from a project to a task, avoiding duplicates.
    """
    for doc_line in project.document_required_type_ids:
        if not task.document_required_type_ids.filtered(lambda l: l.document_id == doc_line.document_id):
            env['project.document.required.line'].sudo().create({
                'task_id': task.id,
                'document_id': doc_line.document_id.id,
                'is_required': doc_line.is_required,
            })
    for doc_line in project.document_type_ids:
        if not task.document_type_ids.filtered(lambda l: l.document_id == doc_line.document_id):
            env['project.document.type.line'].sudo().create({
                'task_id': task.id,
                'document_id': doc_line.document_id.id,
                'is_required': doc_line.is_required,
            }) 