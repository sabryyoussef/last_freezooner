# -*- coding: utf-8 -*-

import logging
from odoo import api, fields, models, _

_logger = logging.getLogger(__name__)


class ProductTemplate(models.Model):
    """
    Product Template Model
    
    Extends product.template to add new_workflow service tracking
    and document tag functionality for the clean module.
    """
    _inherit = 'product.template'
    
    # Service tracking with new_workflow option
    service_tracking = fields.Selection(
        selection_add=[
            ('new_workflow', 'New Workflow'),
        ],
        ondelete={'new_workflow': 'set no'}
    )
    
    # Document tags for this product
    document_tag_ids = fields.Many2many(
        'documents.tag',
        string='Document Tags',
        domain=[('is_project_document', '=', True)],
        help='Document tags that will be required for projects created from this product'
    )
    
    # Task templates
    task_template_ids = fields.One2many(
        'product.task.template',
        'product_tmpl_id',
        string='Task Templates',
        help='Task templates that will be created when this product is added to a project'
    )
    
    @api.model_create_multi
    def create(self, vals_list):
        """Override create to set up default task templates for new_workflow products"""
        templates = super().create(vals_list)
        for template in templates:
            if template.service_tracking == 'new_workflow' and not template.task_template_ids:
                template._create_default_task_templates()
        return templates

    @api.returns('ir.actions.client')
    def action_create_task_templates(self):
        """Manual action to create task templates"""
        self.ensure_one()
        if self.service_tracking == 'new_workflow':
            if self.task_template_ids:
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': _('Info'),
                        'message': _('Task templates already exist for this product'),
                        'type': 'info',
                    }
                }
            else:
                self._create_default_task_templates()
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': _('Success'),
                        'message': _('Task templates created successfully'),
                        'type': 'success',
                    }
                }
        else:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Warning'),
                    'message': _('This product does not have "New Workflow" service tracking'),
                    'type': 'warning',
                }
            }


class ProjectMilestone(models.Model):
    """
    Project Milestone Model
    
    Extends project.milestone to add email template and checkpoint functionality.
    """
    _inherit = 'project.milestone'
    _description = 'Project Milestone'

    mail_template_id = fields.Many2one('mail.template', string='Email Template')
    milestone_message = fields.Text(string='Milestone Message', help='Message to display when milestone is reached')
    checkpoint_ids = fields.One2many('task.checkpoint', 'milestone_id', string='Checkpoints')
    checkpoint_count = fields.Integer(string='Checkpoint Count', compute='_compute_checkpoint_count')
    
    @api.depends('checkpoint_ids')
    def _compute_checkpoint_count(self):
        for milestone in self:
            milestone.checkpoint_count = len(milestone.checkpoint_ids)
    
    def action_view_checkpoints(self):
        """Open the checkpoints view for this milestone"""
        self.ensure_one()
        return {
            'name': f'Checkpoints for {self.name}',
            'type': 'ir.actions.act_window',
            'res_model': 'task.checkpoint',
            'view_mode': 'list,form',
            'domain': [('milestone_id', '=', self.id)],
            'context': {'default_milestone_id': self.id},
        }
    
    def send_milestone_notification(self, task):
        """Send milestone notification when reached"""
        self.ensure_one()
        
        if self.mail_template_id and task.partner_id:
            # Send email notification
            self.mail_template_id.send_mail(task.id, force_send=True)
        
        if self.milestone_message:
            # Post message to task chatter
            task.message_post(
                body=f"🎯 **Milestone Reached**: {self.name}\n\n{self.milestone_message}",
                message_type='notification'
            )
        
        return True


class ReachedCheckpoint(models.Model):
    """
    Reached Checkpoint Model
    
    Base model for defining checkpoints that can be reached in tasks.
    """
    _name = 'reached.checkpoint'
    _description = 'Reached Checkpoint'
    _order = 'sequence, id'
    
    name = fields.Char('Checkpoint Name', required=True)
    description = fields.Text('Description')
    sequence = fields.Integer('Sequence', default=10)
    is_active = fields.Boolean('Active', default=True)


class ProductTaskTemplateCheckpoint(models.Model):
    """
    Product Task Template Checkpoint Model
    
    Defines checkpoint configuration for task templates.
    """
    _name = 'product.task.template.checkpoint'
    _description = 'Product Task Template Checkpoint'
    _order = 'sequence, id'

    task_template_id = fields.Many2one('product.task.template', string='Task Template', required=True, ondelete='cascade')
    checkpoint_ids = fields.Many2many('reached.checkpoint', string='Reached Checkpoints')
    stage_id = fields.Many2one('project.task.type', string='Stage')
    milestone_id = fields.Many2one('project.milestone', string='Milestone')
    sequence = fields.Integer(string='Sequence', default=10)


class TaskCheckpoint(models.Model):
    """
    Task Checkpoint Model
    
    Defines checkpoints for individual tasks.
    """
    _name = 'task.checkpoint'
    _description = 'Task Checkpoint'
    _order = 'sequence, id'

    task_id = fields.Many2one('project.task', string='Task', required=True, ondelete='cascade')
    checkpoint_ids = fields.Many2many('reached.checkpoint', string='Reached Checkpoints')
    stage_id = fields.Many2one('project.task.type', string='Stage')
    milestone_id = fields.Many2one('project.milestone', string='Milestone')
    sequence = fields.Integer(string='Sequence', default=10)


class CheckpointHistory(models.Model):
    """
    Checkpoint History Model
    
    Tracks the history of checkpoint status changes.
    """
    _name = 'checkpoint.history'
    _description = 'Checkpoint History'
    _order = 'date desc'

    task_id = fields.Many2one('project.task', string='Task', required=True)
    checkpoint_name = fields.Char(string='Checkpoint Name', required=True)
    status = fields.Selection([
        ('started', 'Started'),
        ('completed', 'Completed'),
        ('confirmed', 'Confirmed'),
        ('updated', 'Updated')
    ], string='Status', required=True)
    date = fields.Datetime(string='Date', default=fields.Datetime.now)
    user_id = fields.Many2one('res.users', string='User', default=lambda self: self.env.user)
    notes = fields.Text(string='Notes')


class ProductSubtaskTemplate(models.Model):
    """
    Product Subtask Template Model
    
    Defines subtask templates that will be created under parent tasks.
    """
    _name = 'product.subtask.template'
    _description = 'Product Subtask Template'
    _order = 'sequence, id'
    
    name = fields.Char('Subtask Name', required=True)
    description = fields.Text('Description')
    sequence = fields.Integer('Sequence', default=10)
    planned_hours = fields.Float('Planned Hours', default=1.0)
    priority = fields.Selection([
        ('0', 'Low'),
        ('1', 'Normal'),
        ('2', 'High'),
        ('3', 'Very High'),
    ], string='Priority', default='1')
    
    # Parent task template reference
    task_template_id = fields.Many2one(
        'product.task.template',
        string='Parent Task Template',
        required=True,
        ondelete='cascade'
    )
    
    # Stage reference
    stage_id = fields.Many2one(
        'project.task.type',
        string='Stage',
        help='Default stage for subtasks created from this template'
    )
    
    # User assignment
    user_ids = fields.Many2many(
        'res.users',
        string='Assigned Users',
        help='Users to assign to subtasks created from this template'
    )
    
    # Milestone configuration
    milestone_message = fields.Text(
        string='Milestone Message',
        help='Message to log when this subtask is completed'
    )
    
    @api.model_create_multi
    def create(self, vals_list):
        """Override create to log subtask template creation"""
        templates = super().create(vals_list)
        for template in templates:
            _logger.info(f"Created subtask template: {template.name} for task template: {template.task_template_id.name}")
        return templates
    
    def write(self, vals):
        """Override write to set up default task templates when service_tracking changes to new_workflow"""
        result = super().write(vals)
        if vals.get('service_tracking') == 'new_workflow':
            for template in self:
                if not template.task_template_ids:
                    template._create_default_task_templates()
        return result
    
    def _create_default_task_templates(self):
        """Create default task templates for new_workflow products"""
        if self.service_tracking != 'new_workflow':
            return
            
        _logger.info(f"Creating default task templates for product: {self.name}")
        
        default_templates = [
            {
                'name': 'Document Collection',
                'description': 'Collect all required documents from the client',
                'sequence': 10,
                'planned_hours': 2.0,
                'priority': '1'
            },
            {
                'name': 'Document Review',
                'description': 'Review and validate all submitted documents',
                'sequence': 20,
                'planned_hours': 1.0,
                'priority': '2'
            },
            {
                'name': 'Process Completion',
                'description': 'Complete the process and deliver results',
                'sequence': 30,
                'planned_hours': 1.0,
                'priority': '3'
            },
        ]
        
        for template_data in default_templates:
            template_data['product_tmpl_id'] = self.id
            self.env['product.task.template'].create(template_data)
            _logger.info(f"Created task template: {template_data['name']}")
    
    def action_view_document_tags(self):
        """Action to view document tags for this product"""
        self.ensure_one()
        return {
            'name': _('Document Tags for %s') % self.name,
            'type': 'ir.actions.act_window',
            'res_model': 'documents.tag',
            'view_mode': 'tree,form',
            'domain': [('id', 'in', self.document_tag_ids.ids)],
            'context': {
                'default_is_project_document': True,
            },
        }
    
class ProductProduct(models.Model):
    """
    Product Product Model
    
    Extends product.product to inherit service_tracking from product.template
    """
    _inherit = 'product.product'
    
    service_tracking = fields.Selection(
        related="product_tmpl_id.service_tracking",
        store=True,
        readonly=False,
    )
    
    document_tag_ids = fields.Many2many(
        related="product_tmpl_id.document_tag_ids",
        readonly=False,
    )


class ProductTaskTemplate(models.Model):
    """
    Product Task Template Model
    
    Defines task templates that will be created when a product is added to a project.
    """
    _name = 'product.task.template'
    _description = 'Product Task Template'
    _order = 'sequence, id'
    
    name = fields.Char('Task Name', required=True)
    description = fields.Text('Description')
    sequence = fields.Integer('Sequence', default=10)
    planned_hours = fields.Float('Planned Hours', default=1.0)
    priority = fields.Selection([
        ('0', 'Low'),
        ('1', 'Normal'),
        ('2', 'High'),
        ('3', 'Very High'),
    ], string='Priority', default='1')
    
    # Product template reference
    product_tmpl_id = fields.Many2one(
        'product.template',
        string='Product Template',
        required=True,
        ondelete='cascade'
    )
    
    # Stage reference
    stage_id = fields.Many2one(
        'project.task.type',
        string='Stage',
        help='Default stage for tasks created from this template'
    )
    
    # User assignment
    user_ids = fields.Many2many(
        'res.users',
        string='Assigned Users',
        help='Users to assign to tasks created from this template'
    )
    
    # Document tags for this task template
    document_tag_ids = fields.Many2many(
        'documents.tag',
        string='Required Document Tags',
        domain=[('is_project_document', '=', True)],
        help='Document tags that will be required for tasks created from this template'
    )
    
    # Milestone configuration
    milestone_id = fields.Many2one(
        'project.milestone',
        string='Milestone',
        help='Milestone associated with this task template'
    )
    
    milestone_message = fields.Text(
        string='Milestone Message',
        help='Message to log when checkpoint is reached'
    )
    
    # Checkpoint configuration
    checkpoint_field = fields.Selection([
        ('is_complete_return_required', 'Required Document Complete'),
        ('is_complete_return_deliverable', 'Deliverable Document Complete'),
        ('is_complete_return_hand', 'Handover Complete'),
        ('is_complete_return_compliance', 'Compliance Complete'),
        ('is_complete_return_partner_fields', 'Partner Fields Complete'),
    ], string='Checkpoint Field', help='Select a checkpoint field that will act as a boolean checkpoint for individual tasks')
    
    # Subtask configuration
    subtask_ids = fields.One2many(
        'product.subtask.template',
        'task_template_id',
        string='Subtasks',
        help='Subtasks that will be created under this task'
    )
    
    # Checkpoint configuration
    checkpoint_ids = fields.One2many(
        'product.task.template.checkpoint',
        'task_template_id',
        string='Checkpoints',
        help='Checkpoint configuration for this task template'
    )
    
    # Computed fields
    subtask_count = fields.Integer(
        string='Subtask Count',
        compute='_compute_subtask_count',
        help='Number of subtasks for this template'
    )
    
    @api.depends('subtask_ids')
    def _compute_subtask_count(self):
        """Compute the number of subtasks for this template"""
        for template in self:
            template.subtask_count = len(template.subtask_ids)
    
    @api.model_create_multi
    def create(self, vals_list):
        """Override create to log task template creation"""
        templates = super().create(vals_list)
        for template in templates:
            _logger.info(f"Created task template: {template.name} for product: {template.product_tmpl_id.name}")
        return templates