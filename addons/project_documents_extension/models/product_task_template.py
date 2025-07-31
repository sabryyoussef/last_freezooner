from odoo import api
from odoo import models, fields
from odoo.exceptions import ValidationError

class ProductTaskTemplate(models.Model):
    _name = 'product.task.template'
    _description = 'Product Task Template'
    _order = 'sequence, id'

    name = fields.Char(string='Task Name', required=True)
    sequence = fields.Integer(string='Sequence', default=10)
    product_tmpl_id = fields.Many2one('product.template', string='Product Template', required=True, ondelete='cascade')
    description = fields.Text(string='Description')
    user_ids = fields.Many2many('res.users', string='Assignees')
    stage_id = fields.Many2one('project.task.type', string='Initial Stage')
    planned_hours = fields.Float(string='Planned Hours')
    priority = fields.Selection([('0', 'Low'), ('1', 'High')], string='Priority', default='0')
    subtask_ids = fields.One2many('product.subtask.template', 'task_template_id', string='Subtasks')
    subtask_count = fields.Integer(string='Subtask Count', compute='_compute_subtask_count')
    checkpoint_ids = fields.One2many(
        'product.task.template.checkpoint', 'task_template_id', string='Reached Checkpoints'
    )

    def _compute_subtask_count(self):
        for template in self:
            template.subtask_count = len(template.subtask_ids)

class ProductSubtaskTemplate(models.Model):
    _name = 'product.subtask.template'
    _description = 'Product Subtask Template'
    _order = 'sequence, id'

    name = fields.Char(string='Subtask Name', required=True)
    sequence = fields.Integer(string='Sequence', default=10)
    task_template_id = fields.Many2one('product.task.template', string='Parent Task Template', required=True, ondelete='cascade')
    description = fields.Text(string='Description')
    user_ids = fields.Many2many('res.users', string='Assignees')
    stage_id = fields.Many2one('project.task.type', string='Initial Stage')
    planned_hours = fields.Float(string='Planned Hours')
    priority = fields.Selection([('0', 'Low'), ('1', 'High')], string='Priority', default='0')
    milestone_message = fields.Text(string='Milestone Message')

class ProductTaskTemplateCheckpoint(models.Model):
    _name = 'product.task.template.checkpoint'
    _description = 'Product Task Template Checkpoint'
    _order = 'sequence, id'

    task_template_id = fields.Many2one('product.task.template', string='Task Template', required=True, ondelete='cascade')
    checkpoint_ids = fields.Many2many('reached.checkpoint', string='Reached Checkpoints')
    stage_id = fields.Many2one('project.task.type', string='Stage')
    milestone_id = fields.Many2one('project.milestone', string='Milestone')
    sequence = fields.Integer(string='Sequence', default=10)

class TaskCheckpoint(models.Model):
    _name = 'task.checkpoint'
    _description = 'Task Checkpoint'
    _order = 'sequence, id'

    task_id = fields.Many2one('project.task', string='Task', required=True, ondelete='cascade')
    checkpoint_ids = fields.Many2many('reached.checkpoint', string='Reached Checkpoints')
    stage_id = fields.Many2one('project.task.type', string='Stage')
    milestone_id = fields.Many2one('project.milestone', string='Milestone')
    sequence = fields.Integer(string='Sequence', default=10)

class ProjectTask(models.Model):
    _inherit = 'project.task'

    task_checkpoint_ids = fields.One2many('task.checkpoint', 'task_id', string='Checkpoints')
    milestone_ids = fields.Many2many('project.milestone', string='Milestones')
    
    # Handover checkpoints
    is_complete_return_hand = fields.Selection([
        ('not_started', 'Not Started'),
        ('in_progress', 'In Progress'),
        ('complete', 'Complete'),
        ('confirmed', 'Confirmed'),
        ('updated', 'Updated')
    ], string="Handover Complete", default='not_started')
    
    is_confirm_hand = fields.Selection([
        ('not_started', 'Not Started'),
        ('in_progress', 'In Progress'),
        ('complete', 'Complete'),
        ('confirmed', 'Confirmed'),
        ('updated', 'Updated')
    ], string="Handover Confirm", default='not_started')
    
    is_update_hand = fields.Selection([
        ('not_started', 'Not Started'),
        ('in_progress', 'In Progress'),
        ('complete', 'Complete'),
        ('confirmed', 'Confirmed'),
        ('updated', 'Updated')
    ], string="Update Handover", default='not_started')

    # Compliance checkpoints
    is_complete_return_compliance = fields.Selection([
        ('not_started', 'Not Started'),
        ('in_progress', 'In Progress'),
        ('complete', 'Complete'),
        ('confirmed', 'Confirmed'),
        ('updated', 'Updated')
    ], string="Compliance Complete", default='not_started')
    
    is_confirm_compliance = fields.Selection([
        ('not_started', 'Not Started'),
        ('in_progress', 'In Progress'),
        ('complete', 'Complete'),
        ('confirmed', 'Confirmed'),
        ('updated', 'Updated')
    ], string="Compliance Confirm", default='not_started')
    
    is_update_compliance = fields.Selection([
        ('not_started', 'Not Started'),
        ('in_progress', 'In Progress'),
        ('complete', 'Complete'),
        ('confirmed', 'Confirmed'),
        ('updated', 'Updated')
    ], string="Update Compliance", default='not_started')

    # Required document checkpoints
    is_complete_return_required = fields.Selection([
        ('not_started', 'Not Started'),
        ('in_progress', 'In Progress'),
        ('complete', 'Complete'),
        ('confirmed', 'Confirmed'),
        ('updated', 'Updated')
    ], string="Required Document Complete", default='not_started')
    
    is_confirm_required = fields.Selection([
        ('not_started', 'Not Started'),
        ('in_progress', 'In Progress'),
        ('complete', 'Complete'),
        ('confirmed', 'Confirmed'),
        ('updated', 'Updated')
    ], string="Required Document Confirm", default='not_started')
    
    is_update_required = fields.Selection([
        ('not_started', 'Not Started'),
        ('in_progress', 'In Progress'),
        ('complete', 'Complete'),
        ('confirmed', 'Confirmed'),
        ('updated', 'Updated')
    ], string="Update Required Document", default='not_started')

    # Deliverable document checkpoints
    is_complete_return_deliverable = fields.Selection([
        ('not_started', 'Not Started'),
        ('in_progress', 'In Progress'),
        ('complete', 'Complete'),
        ('confirmed', 'Confirmed'),
        ('updated', 'Updated')
    ], string="Deliverable Document Complete", default='not_started')
    
    is_confirm_deliverable = fields.Selection([
        ('not_started', 'Not Started'),
        ('in_progress', 'In Progress'),
        ('complete', 'Complete'),
        ('confirmed', 'Confirmed'),
        ('updated', 'Updated')
    ], string="Deliverable Document Confirm", default='not_started')
    
    is_update_deliverable = fields.Selection([
        ('not_started', 'Not Started'),
        ('in_progress', 'In Progress'),
        ('complete', 'Complete'),
        ('confirmed', 'Confirmed'),
        ('updated', 'Updated')
    ], string="Update Deliverable Document", default='not_started')

    # Partner fields checkpoints
    is_complete_return_partner_fields = fields.Selection([
        ('not_started', 'Not Started'),
        ('in_progress', 'In Progress'),
        ('complete', 'Complete'),
        ('confirmed', 'Confirmed'),
        ('updated', 'Updated')
    ], string="Partner Fields Complete", default='not_started')
    
    is_confirm_partner_fields = fields.Selection([
        ('not_started', 'Not Started'),
        ('in_progress', 'In Progress'),
        ('complete', 'Complete'),
        ('confirmed', 'Confirmed'),
        ('updated', 'Updated')
    ], string="Partner Fields Confirm", default='not_started')
    
    is_update_partner_fields = fields.Selection([
        ('not_started', 'Not Started'),
        ('in_progress', 'In Progress'),
        ('complete', 'Complete'),
        ('confirmed', 'Confirmed'),
        ('updated', 'Updated')
    ], string="Update Partner Fields", default='not_started')

    # Additional checkpoints
    is_document_collection_complete = fields.Selection([
        ('not_started', 'Not Started'),
        ('in_progress', 'In Progress'),
        ('complete', 'Complete')
    ], string="Document Collection Complete", default='not_started')
    
    is_process_complete = fields.Selection([
        ('not_started', 'Not Started'),
        ('in_progress', 'In Progress'),
        ('complete', 'Complete')
    ], string="Process Complete", default='not_started')

    # --- Workflow checkboxes for Required Documents ---
    required_document_complete = fields.Boolean(string="Required Document Complete", default=False)
    required_document_confirm = fields.Boolean(string="Required Document Confirm", default=False)
    required_document_update = fields.Boolean(string="Required Document Update", default=False)

    # --- Workflow checkboxes for Deliverable Documents ---
    deliverable_document_complete = fields.Boolean(string="Deliverable Document Complete", default=False)
    deliverable_document_confirm = fields.Boolean(string="Deliverable Document Confirm", default=False)
    deliverable_document_update = fields.Boolean(string="Deliverable Document Update", default=False)

    def _validate_documents_uploaded(self):
        missing_docs = []
        # Check required documents
        for line in self.document_required_type_ids:
            if getattr(line, 'is_required', False):
                # Check for attachments on the document line
                has_attachment = False
                if hasattr(line, 'attachment_ids') and line.attachment_ids:
                    has_attachment = True
                # Check for attachments on the project/task
                if not has_attachment:
                    attachments = self.env['ir.attachment'].search([
                        ('res_model', '=', self._name),
                        ('res_id', '=', self.id),
                        ('name', '=', line.document_id.name)
                    ], limit=1)
                    if attachments:
                        has_attachment = True
                if not has_attachment:
                    missing_docs.append(line.document_id.display_name or line.document_id.name or 'Unknown Document')
        # Check deliverable documents
        for line in self.document_type_ids:
            if getattr(line, 'is_required', False):
                has_attachment = False
                if hasattr(line, 'attachment_ids') and line.attachment_ids:
                    has_attachment = True
                if not has_attachment:
                    attachments = self.env['ir.attachment'].search([
                        ('res_model', '=', self._name),
                        ('res_id', '=', self.id),
                        ('name', '=', line.document_id.name)
                    ], limit=1)
                    if attachments:
                        has_attachment = True
                if not has_attachment:
                    missing_docs.append(line.document_id.display_name or line.document_id.name or 'Unknown Document')
        if missing_docs:
            raise ValidationError(
                "You must upload the following required/deliverable documents before completing this action:\n- " + "\n- ".join(missing_docs)
            )

    def write(self, vals):
        # Prevent recursion
        if self.env.context.get('no_checkpoint_write'):
            return super().write(vals)

        checkpoint_map = {
            'is_complete_return_hand': 'Handover Complete',
            'is_confirm_hand': 'Handover Confirm',
            'is_update_hand': 'Update Handover',
            'is_complete_return_compliance': 'Compliance Complete',
            'is_confirm_compliance': 'Compliance Confirm',
            'is_update_compliance': 'Update Compliance',
            'is_complete_return_required': 'Required Document Complete',
            'is_confirm_required': 'Required Document Confirm',
            'is_update_required': 'Update Required Document',
            'is_complete_return_deliverable': 'Deliverable Document Complete',
            'is_confirm_deliverable': 'Deliverable Document Confirm',
            'is_update_deliverable': 'Update Deliverable Document',
            'is_complete_return_partner_fields': 'Partner Fields Complete',
            'is_confirm_partner_fields': 'Partner Fields Confirm',
            'is_update_partner_fields': 'Update Partner Fields',
            'is_document_collection_complete': 'Document Collection Complete',
            'is_process_complete': 'Process Complete',
        }

        # Copy vals to avoid mutating the original dict
        vals = vals.copy()

        # --- Document validation logic on checkpoint field change ---
        for field in ['is_complete_return_required', 'is_confirm_required', 'is_update_required',
                      'is_complete_return_deliverable', 'is_confirm_deliverable', 'is_update_deliverable']:
            if field in vals:
                if vals[field] in ['complete', 'confirmed', 'updated']:
                    self._validate_documents_uploaded()

        for task in self:
            for checkpoint_line in task.task_checkpoint_ids:
                for field, checkpoint_name in checkpoint_map.items():
                    if checkpoint_name in checkpoint_line.checkpoint_ids.mapped('name'):
                        field_value = vals.get(field, getattr(task, field))
                        if field_value in ['complete', 'confirmed', 'updated']:
                            if checkpoint_line.stage_id and (vals.get('stage_id', task.stage_id.id) != checkpoint_line.stage_id.id):
                                vals['stage_id'] = checkpoint_line.stage_id.id

        return super(ProjectTask, self.with_context(no_checkpoint_write=True)).write(vals)

    def update_checkpoint_status(self, checkpoint_field, status):
        """
        Update a specific checkpoint field status
        Args:
            checkpoint_field (str): Field name to update (e.g., 'is_complete_return_hand')
            status (str): New status ('not_started', 'in_progress', 'complete', 'confirmed', 'updated')
        """
        if hasattr(self, checkpoint_field):
            self.write({checkpoint_field: status})
            return True
        return False

    def complete_checkpoint(self, checkpoint_field):
        self._validate_documents_uploaded()
        return self.update_checkpoint_status(checkpoint_field, 'complete')

    def confirm_checkpoint(self, checkpoint_field):
        self._validate_documents_uploaded()
        return self.update_checkpoint_status(checkpoint_field, 'confirmed')

    def update_checkpoint(self, checkpoint_field):
        self._validate_documents_uploaded()
        return self.update_checkpoint_status(checkpoint_field, 'updated')

    def start_checkpoint(self, checkpoint_field):
        """Set a checkpoint to in progress status"""
        return self.update_checkpoint_status(checkpoint_field, 'in_progress')

    def reset_checkpoint(self, checkpoint_field):
        """Reset a checkpoint to not started status"""
        return self.update_checkpoint_status(checkpoint_field, 'not_started') 

    # --- Button Actions for Required Documents ---
    def action_complete_required_documents(self):
        self._validate_documents_uploaded()
        self.is_complete_return_required = 'complete'
        self.required_document_complete = True

    def action_confirm_required_documents(self):
        self._validate_documents_uploaded()
        self.is_confirm_required = 'confirmed'
        self.required_document_confirm = True

    def action_update_required_documents(self):
        self._validate_documents_uploaded()
        self.is_update_required = 'updated'
        self.required_document_update = True

    def action_reset_required_document_complete(self):
        self.required_document_complete = False
        self.is_complete_return_required = 'not_started'

    def action_reset_required_document_confirm(self):
        self.required_document_confirm = False
        self.is_confirm_required = 'not_started'

    def action_reset_required_document_update(self):
        self.required_document_update = False
        self.is_update_required = 'not_started'

    # --- Button Actions for Deliverable Documents ---
    def action_complete_deliverable_documents(self):
        self._validate_documents_uploaded()
        self.is_complete_return_deliverable = 'complete'
        self.deliverable_document_complete = True

    def action_confirm_deliverable_documents(self):
        self._validate_documents_uploaded()
        self.is_confirm_deliverable = 'confirmed'
        self.deliverable_document_confirm = True

    def action_update_deliverable_documents(self):
        self._validate_documents_uploaded()
        self.is_update_deliverable = 'updated'
        self.deliverable_document_update = True

    def action_reset_deliverable_document_complete(self):
        self.deliverable_document_complete = False
        self.is_complete_return_deliverable = 'not_started'

    def action_reset_deliverable_document_confirm(self):
        self.deliverable_document_confirm = False
        self.is_confirm_deliverable = 'not_started'

    def action_reset_deliverable_document_update(self):
        self.deliverable_document_update = False
        self.is_update_deliverable = 'not_started' 

    def action_trigger_milestone_notification(self, milestone):
        """Trigger milestone notification for this task"""
        self.ensure_one()
        if milestone:
            milestone.send_milestone_notification(self)
            self.message_post(
                body=f"🎯 **Milestone Reached**: {milestone.name}\n\n{milestone.milestone_message or 'Milestone completed successfully.'}",
                message_type='notification'
            )
        return True

    def action_complete_checkpoint_with_milestone(self, checkpoint_name):
        """Complete a checkpoint and trigger milestone notification if applicable"""
        self.ensure_one()
        
        # Find the checkpoint
        checkpoint = self.task_checkpoint_ids.filtered(
            lambda c: checkpoint_name in c.checkpoint_ids.mapped('name')
        )[:1]
        
        if checkpoint and checkpoint.milestone_id:
            # Trigger milestone notification
            checkpoint.milestone_id.send_milestone_notification(self)
            
            # Log checkpoint completion
            self.message_post(
                body=f"✅ **Checkpoint Completed**: {checkpoint_name}\n\nMilestone: {checkpoint.milestone_id.name}",
                message_type='notification'
            )
            
            return True
        
        return False

    def action_complete_checkpoint_with_milestone_simple(self):
        """Simple action to complete checkpoint with milestone (no parameters)"""
        self.ensure_one()
        
        # Find any checkpoint with a milestone
        checkpoint = self.task_checkpoint_ids.filtered(
            lambda c: c.milestone_id
        )[:1]
        
        if checkpoint:
            checkpoint_name = checkpoint.checkpoint_ids.mapped('name')[0] if checkpoint.checkpoint_ids else "Checkpoint"
            return self.action_complete_checkpoint_with_milestone(checkpoint_name)
        else:
            # Show notification that no milestone-linked checkpoints found
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'No Milestone Checkpoints',
                    'message': 'No checkpoints with linked milestones found for this task.',
                    'type': 'warning'
                }
            }

    def action_get_task_milestone_progress(self):
        """Get milestone progress for this task"""
        self.ensure_one()
        milestones = self.milestone_ids
        total_milestones = len(milestones)
        completed_milestones = len(milestones.filtered(lambda m: m.is_reached))
        
        progress = {
            'total': total_milestones,
            'completed': completed_milestones,
            'percentage': (completed_milestones / total_milestones * 100) if total_milestones > 0 else 0,
            'milestones': milestones.mapped('name'),
            'completed_milestones': completed_milestones.mapped('name'),
            'pending_milestones': milestones.filtered(lambda m: not m.is_reached).mapped('name'),
        }
        
        return progress

class TaskDocumentRequiredLines(models.Model):
    _name = 'task.document.required.lines'
    _description = 'Task Document Required Lines'

    project_id = fields.Many2one('project.project', string='Project', ondelete='cascade')
    task_id = fields.Many2one('project.task', string='Task', ondelete='cascade')
    document_id = fields.Many2one('project.document.type', string='Document Type', required=True)
    name = fields.Char(string='Document Name')
    is_required = fields.Boolean(string='Required', default=False)
    is_verified = fields.Boolean(string='Verified', default=False)
    verification_date = fields.Date(string='Verification Date')
    verified_by = fields.Many2one('res.users', string='Verified By')
    is_moved = fields.Boolean(string='Is Moved', default=False)
    is_ready = fields.Boolean(string='Is Ready', default=False)
    issue_date = fields.Date('Issue Date')
    expiration_date = fields.Date('Expiration Date')
    document = fields.Binary(string='Document')

class ProductTemplateRequiredDocuments(models.Model):
    _name = 'product.template.required.documents'
    _description = 'Product Template Required Documents'

    rating_id = fields.Many2one('risk.rating', string='Rating')
    product_tmpl_id = fields.Many2one(
        "product.template",
        string="Product Template",
        required=False,  # Make it optional
        ondelete="cascade",
        index=True,
    )
    document_id = fields.Many2one('project.document.type', string='Document Type', required=True)
    is_required = fields.Boolean(string='Required', default=False)
    
    @api.constrains('product_tmpl_id', 'rating_id')
    def _check_required_reference(self):
        """Ensure either product_tmpl_id or rating_id is set"""
        for record in self:
            if not record.product_tmpl_id and not record.rating_id:
                raise ValidationError(
                    "Either Product Template or Rating must be set."
                ) 

class CheckpointHistory(models.Model):
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