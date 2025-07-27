from odoo import models, api
import logging

_logger = logging.getLogger(__name__)


class TaskCheckpointService(models.AbstractModel):
    """
    Task Checkpoint Service
    Handles copying checkpoint configurations from product task templates to project tasks
    """
    _name = 'task.checkpoint.service'
    _description = 'Task Checkpoint Service'

    @api.model
    def copy_checkpoints_from_template(self, task, template):
        """
        Copy checkpoint configurations from product task template to project task
        
        Args:
            task: project.task record
            template: product.task.template record
        """
        try:
            if not template.checkpoint_ids:
                return
            
            for template_checkpoint in template.checkpoint_ids:
                task_checkpoint_vals = {
                    'task_id': task.id,
                    'checkpoint_ids': [(6, 0, template_checkpoint.checkpoint_ids.ids)],
                    'stage_id': template_checkpoint.stage_id.id if template_checkpoint.stage_id else False,
                    'milestone_id': template_checkpoint.milestone_id.id if template_checkpoint.milestone_id else False,
                    'sequence': template_checkpoint.sequence or 10,
                }
                
                task_checkpoint = self.env['task.checkpoint'].create(task_checkpoint_vals)
                
        except Exception as e:
            _logger.error(f"Error copying checkpoint configurations from template {template.name} to task {task.name}: {e}")

    @api.model
    def create_task_with_checkpoints(self, project, template):
        """
        Create a project task from template with checkpoint configurations
        
        Args:
            project: project.project record
            template: product.task.template record
            
        Returns:
            project.task record or None if creation fails
        """
        try:
            # Prepare task values
            task_vals = {
                'name': template.name,
                'project_id': project.id,
                'description': template.description or '',
                'user_ids': [(6, 0, template.user_ids.ids)],
                'allocated_hours': template.planned_hours or 0.0,
                'priority': template.priority if template.priority in ['0', '1'] else '0',
            }
            
            # Set initial stage if specified
            if template.stage_id:
                if template.stage_id.id in project.type_ids.ids:
                    task_vals['stage_id'] = template.stage_id.id
                else:
                    # Use project's default stage
                    default_stage = project.type_ids.filtered(lambda s: not s.fold)[:1]
                    if default_stage:
                        task_vals['stage_id'] = default_stage.id
            
            # Create the task
            task = self.env['project.task'].create(task_vals)
            
            # Copy checkpoint configurations from template
            if template.checkpoint_ids:
                self.copy_checkpoints_from_template(task, template)
            
            # Log task creation
            creation_message = f"""
                <b>Task Created from Template:</b><br/>
                • Template: {template.name}<br/>
                • Stage: {task.stage_id.name if task.stage_id else 'Not set'}<br/>
                • Planned Hours: {template.planned_hours or 0}<br/>
                • Priority: {template.priority or 'Normal'}<br/>
                • Assigned Users: {len(template.user_ids)}<br/>
                • Checkpoint Configurations: {len(template.checkpoint_ids)}
            """
            task.message_post(body=creation_message)
            
            return task
            
        except Exception as e:
            _logger.error(f"Error creating task from template {template.name}: {e}")
            return None

    @api.model
    def create_tasks_from_templates(self, project, templates):
        """
        Create multiple tasks from templates with checkpoint configurations
        
        Args:
            project: project.project record
            templates: product.task.template recordset
            
        Returns:
            list of created project.task records
        """
        created_tasks = []
        
        for template in templates:
            task = self.create_task_with_checkpoints(project, template)
            if task:
                created_tasks.append(task)
        
        return created_tasks 