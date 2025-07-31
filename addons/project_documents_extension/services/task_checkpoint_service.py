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
                
                # If milestone is assigned, link it to the task
                if template_checkpoint.milestone_id:
                    task.milestone_id = template_checkpoint.milestone_id.id
                    _logger.info(f"Milestone '{template_checkpoint.milestone_id.name}' assigned to task '{task.name}'")
                
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
                {f'<br/>• Milestone: {task.milestone_id.name}' if task.milestone_id else ''}
            """
            task.message_post(body=creation_message)
            
            return task
            
        except Exception as e:
            _logger.error(f"Error creating task from template {template.name}: {e}")
            return None

    @api.model
    def trigger_milestone_notification(self, task, milestone):
        """
        Trigger milestone notification when checkpoint is completed
        
        Args:
            task: project.task record
            milestone: project.milestone record
        """
        try:
            if milestone and task:
                # Send milestone notification
                milestone.send_milestone_notification(task)
                
                # Log milestone reached
                task.message_post(
                    body=f"🎯 **Milestone Reached**: {milestone.name}\n\n{milestone.milestone_message or 'Milestone completed successfully.'}",
                    message_type='notification'
                )
                
                _logger.info(f"Milestone notification sent for task '{task.name}' and milestone '{milestone.name}'")
                
        except Exception as e:
            _logger.error(f"Error triggering milestone notification for task {task.name}: {e}")

    @api.model
    def complete_checkpoint_with_milestone(self, task, checkpoint_name):
        """
        Complete a checkpoint and trigger milestone notification if applicable
        
        Args:
            task: project.task record
            checkpoint_name: string name of the checkpoint
        """
        try:
            # Find the checkpoint
            checkpoint = task.task_checkpoint_ids.filtered(
                lambda c: checkpoint_name in c.checkpoint_ids.mapped('name')
            )[:1]
            
            if checkpoint and checkpoint.milestone_id:
                # Trigger milestone notification
                self.trigger_milestone_notification(task, checkpoint.milestone_id)
                
                # Log checkpoint completion
                task.message_post(
                    body=f"✅ **Checkpoint Completed**: {checkpoint_name}\n\nMilestone: {checkpoint.milestone_id.name}",
                    message_type='notification'
                )
                
                _logger.info(f"Checkpoint '{checkpoint_name}' completed for task '{task.name}' with milestone '{checkpoint.milestone_id.name}'")
            
        except Exception as e:
            _logger.error(f"Error completing checkpoint '{checkpoint_name}' for task {task.name}: {e}")

    @api.model
    def get_milestone_progress(self, project):
        """
        Get milestone progress for a project
        
        Args:
            project: project.project record
            
        Returns:
            dict with milestone progress information
        """
        try:
            milestones = project.milestone_ids
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
            
        except Exception as e:
            _logger.error(f"Error getting milestone progress for project {project.name}: {e}")
            return {}

    @api.model
    def send_milestone_summary_email(self, project):
        """
        Send milestone summary email for a project
        
        Args:
            project: project.project record
        """
        try:
            if project.partner_id and project.milestone_ids:
                # Get milestone summary template
                template = self.env.ref('project_documents_extension.email_template_milestone_summary', raise_if_not_found=False)
                
                if template:
                    template.send_mail(project.id, force_send=True)
                    _logger.info(f"Milestone summary email sent for project '{project.name}'")
                else:
                    _logger.warning("Milestone summary email template not found")
                    
        except Exception as e:
            _logger.error(f"Error sending milestone summary email for project {project.name}: {e}") 