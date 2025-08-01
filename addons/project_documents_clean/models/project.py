# -*- coding: utf-8 -*-

from odoo import api, fields, models, _


class ProjectProject(models.Model):
    """
    Project Project Model
    
    This model extends project.project to add document functionality.
    """
    _inherit = 'project.project'
    
    # Document-related fields
    document_ids = fields.One2many(
        'documents.document',
        'project_id',
        string='Project Documents',
        help='Documents associated with this project'
    )
    
    document_count = fields.Integer(
        string='Document Count',
        compute='_compute_document_count',
        help='Number of documents in this project'
    )
    
    # Document folder
    documents_folder_id = fields.Many2one(
        'documents.document',
        string="Documents Folder",
        copy=False,
        domain="[('type', '=', 'folder')]",
        help="Folder in which project documents will be stored"
    )
    
    @api.depends('document_ids')
    def _compute_document_count(self):
        """Compute the number of documents in this project"""
        for project in self:
            project.document_count = len(project.document_ids)
    
    def action_view_documents(self):
        """Action to view project documents"""
        self.ensure_one()
        return {
            'name': _('Project Documents'),
            'type': 'ir.actions.act_window',
            'res_model': 'documents.document',
            'view_mode': 'kanban,tree,form',
            'domain': [('project_id', '=', self.id)],
            'context': {
                'default_project_id': self.id,
            },
        }
    
    def update_stage_from_template(self, template):
        """Update project stage based on task template configuration"""
        if template.update_project_stage and template.project_stage_id:
            self.stage_id = template.project_stage_id.id
            self.message_post(
                body=_(
                    '🔄 Project stage updated to "%s" based on task template "%s"'
                ) % (template.project_stage_id.name, template.name)
            )
    
    def action_create_document_folder(self):
        """Create a documents folder for this project"""
        self.ensure_one()
        if not self.documents_folder_id:
            folder = self.env['documents.document'].create({
                'name': self.name,
                'type': 'folder',
                'company_id': self.company_id.id if self.company_id else False,
            })
            self.documents_folder_id = folder.id
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Success'),
                    'message': _('Documents folder created successfully'),
                    'type': 'success',
                }
            }
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Info'),
                'message': _('Documents folder already exists'),
                'type': 'info',
            }
        }


class ProjectTask(models.Model):
    """
    Project Task Model
    
    This model extends project.task to add document functionality.
    """
    _inherit = 'project.task'
    
    # Document-related fields
    document_ids = fields.One2many(
        'documents.document',
        'task_id',
        string='Task Documents',
        help='Documents associated with this task'
    )
    
    document_count = fields.Integer(
        string='Document Count',
        compute='_compute_document_count',
        help='Number of documents in this task'
    )
    
    # Checkpoint-related fields
    checkpoint_ids = fields.One2many(
        'task.checkpoint',
        'task_id',
        string='Checkpoints',
        help='Checkpoints for this task'
    )
    
    checkpoint_history_ids = fields.One2many(
        'checkpoint.history',
        'task_id',
        string='Checkpoint History',
        help='History of checkpoint changes'
    )
    
    @api.depends('document_ids')
    def _compute_document_count(self):
        """Compute the number of documents in this task"""
        for task in self:
            task.document_count = len(task.document_ids)
    
    def action_view_documents(self):
        """Action to view task documents"""
        self.ensure_one()
        return {
            'name': _('Task Documents'),
            'type': 'ir.actions.act_window',
            'res_model': 'documents.document',
            'view_mode': 'kanban,tree,form',
            'domain': [('task_id', '=', self.id)],
            'context': {
                'default_task_id': self.id,
                'default_project_id': self.project_id.id,
            },
        } 