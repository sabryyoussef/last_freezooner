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
            _logger.info(f"Starting checkpoint copy process. Template: {template._name} ({template.id}), Task: {task._name} ({task.id})")
            
            if not template.checkpoint_ids:
                _logger.info(f"No checkpoint configurations found in template {template.name}")
                return
            
            _logger.info(f"Copying {len(template.checkpoint_ids)} checkpoint configurations from template {template.name} to task {task.name}")
            _logger.info(f"Template model: {template._name}, fields: {template._fields.keys()}")
            
            created_checkpoints = []
            for template_checkpoint in template.checkpoint_ids:
                # Create task checkpoint record
                # Prepare checkpoint values
                task_checkpoint_vals = {
                    'task_id': task.id,
                    'project_id': task.project_id.id if task.project_id else False,
                    'checkpoint_ids': [(6, 0, template_checkpoint.checkpoint_ids.ids)],
                    'stage_id': template_checkpoint.stage_id.id if template_checkpoint.stage_id else False,
                    'milestone_id': template_checkpoint.milestone_id.id if template_checkpoint.milestone_id else False,
                    'sequence': template_checkpoint.sequence or 10,
                }
                
                _logger.info(f"Creating checkpoint with values: {task_checkpoint_vals}")
                _logger.info(f"Template checkpoint details - ID: {template_checkpoint.id}, Name: {template_checkpoint.display_name}")
                
                task_checkpoint = self.env['task.checkpoint'].create(task_checkpoint_vals)
                _logger.info(f"Created checkpoint record: {task_checkpoint.id} for task {task.name}")
                created_checkpoints.append(task_checkpoint.id)
                _logger.info(f"Created task checkpoint {task_checkpoint.id} for task {task.name} with {len(template_checkpoint.checkpoint_ids)} reached checkpoints")
                
                # Log full checkpoint details for debugging
                _logger.info(f"Checkpoint details - Task: {task._name} (ID: {task.id})")
                _logger.info(f"Available fields on task: {list(task._fields.keys())}")
                _logger.info(f"Task related fields: project_id={task.project_id.id}, sale_order_id={task.sale_order_id.id if task.sale_order_id else None}")
                
                # If milestone is assigned, link it to the task
                if template_checkpoint.milestone_id:
                    task.milestone_id = template_checkpoint.milestone_id.id
                    _logger.info(f"Milestone '{template_checkpoint.milestone_id.name}' assigned to task '{task.name}'")
            
            # Verify the checkpoints are properly linked to the task
            self.env.cache.clear()  # Clear entire cache
            task = task.with_context(prefetch_fields=False).browse(task.id)  # Re-browse to get fresh record
            actual_checkpoints = task.task_checkpoint_ids
            _logger.info(f"Task {task.name} now has {len(actual_checkpoints)} checkpoint records: {[cp.id for cp in actual_checkpoints]}")
            _logger.info(f"Created checkpoint IDs: {created_checkpoints}")
            
            # Force refresh the task record to ensure the view updates
            self.env.cr.commit()  # Commit the transaction to ensure changes are visible
            _logger.info(f"Task checkpoint cache invalidated and transaction committed")
            
        except Exception as e:
            _logger.error(f"Error copying checkpoint configurations from template {template.name} to task {task.name}: {e}")
            import traceback
            _logger.error(f"Full traceback: {traceback.format_exc()}")

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
            _logger.info(f"Creating task from template: {template.name} (ID: {template.id})")
            _logger.info(f"Template checkpoint configurations: {len(template.checkpoint_ids) if template.checkpoint_ids else 0}")
            _logger.info(f"Project details - ID: {project.id}, Name: {project.name}")
            _logger.info(f"Project sale order: {project.sale_order_id.id if project.sale_order_id else None}")
            
            if project.sale_order_id:
                _logger.info(f"Sale order lines: {project.sale_order_id.order_line.mapped('id')}")
                for line in project.sale_order_id.order_line:
                    _logger.info(f"Order line {line.id}: Product={line.product_id.id}, Template={line.product_template_id.id if line.product_template_id else None}")
            
            # Get sale order information
            sale_order = project.sale_order_id
            _logger.info(f"Project sale order: {sale_order.id if sale_order else None}")
            
            # Prepare task values
            task_vals = {
                'name': template.name,
                'project_id': project.id,
                'description': template.description or '',
                'user_ids': [(6, 0, template.user_ids.ids)],
                'allocated_hours': template.planned_hours or 0.0,
                'priority': template.priority if template.priority in ['0', '1'] else '0',
            }
            
            # Try to find matching sale order line and set sale-related fields
            if sale_order:
                task_vals.update({
                    'sale_order_id': sale_order.id,
                    'project_sale_order_id': sale_order.id,
                })
                
                # Find matching sale order line
                product_tmpl_id = template.product_tmpl_id.id if template.product_tmpl_id else None
                _logger.info(f"Looking for sale order line with product_template_id: {product_tmpl_id}")
                
                for line in sale_order.order_line:
                    line_tmpl_id = line.product_template_id.id if line.product_template_id else None
                    _logger.info(f"Checking line {line.id} - Product: {line.product_id.id}, Template: {line_tmpl_id}")
                    
                    if line_tmpl_id and line_tmpl_id == product_tmpl_id:
                        _logger.info(f"Found matching sale order line: {line.id}")
                        task_vals['sale_line_id'] = line.id
                        task_vals['product_id'] = line.product_id.id
                        break
            
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
            _logger.info(f"Created task: {task.name} (ID: {task.id})")
            
            # Copy checkpoint configurations from template
            if template.checkpoint_ids:
                _logger.info(f"Starting checkpoint copy process for task {task.name}")
                self.copy_checkpoints_from_template(task, template)
                
                # Verify checkpoints were copied
                task_checkpoints = task.task_checkpoint_ids
                _logger.info(f"Task {task.name} now has {len(task_checkpoints)} checkpoint configurations")
                for checkpoint in task_checkpoints:
                    _logger.info(f"  - Checkpoint {checkpoint.id}: {len(checkpoint.checkpoint_ids)} reached checkpoints")
            else:
                _logger.warning(f"No checkpoint configurations found in template {template.name}")
            
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
            import traceback
            _logger.error(f"Full traceback: {traceback.format_exc()}")
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
    def handle_document_completion(self, task, action_type):
        """
        Handle document completion events and trigger appropriate checkpoint updates
        
        Args:
            task: project.task record
            action_type: string, either 'complete' or 'confirm'
        """
        try:
            _logger.info(f"🔧 Handling document {action_type} for task {task.name}")
            
            # Map document actions to checkpoint names
            checkpoint_map = {
                'complete': 'Required Document Complete',
                'confirm': 'Required Document Confirm'
            }
            
            checkpoint_name = checkpoint_map.get(action_type)
            if checkpoint_name:
                _logger.info(f"Triggering checkpoint: {checkpoint_name}")
                self.complete_checkpoint_with_milestone(task, checkpoint_name)
            
        except Exception as e:
            _logger.error(f"Error handling document {action_type} for task {task.name}: {e}")
            import traceback
            _logger.error(f"Full traceback: {traceback.format_exc()}")

    @api.model
    def complete_checkpoint_with_milestone(self, task, checkpoint_name):
        """
        Complete a checkpoint and handle stage transition and milestone notifications
        
        Args:
            task: project.task record
            checkpoint_name: string name of the checkpoint
        """
        try:
            _logger.info(f"🔍 Looking for checkpoint '{checkpoint_name}' in task '{task.name}' (ID: {task.id})")
            _logger.info(f"Task has {len(task.task_checkpoint_ids)} checkpoint configurations")
            
            # Log all available checkpoints for debugging
            for cp in task.task_checkpoint_ids:
                _logger.info(f"  - Checkpoint {cp.id}: {cp.checkpoint_ids.mapped('name')}, Stage: {cp.stage_id.name if cp.stage_id else 'None'}, Milestone: {cp.milestone_id.name if cp.milestone_id else 'None'}")
            
            # Find the checkpoint - try multiple ways to match
            checkpoint = None
            
            # Log all reached checkpoints for debugging
            _logger.info("Available Reached Checkpoints:")
            reached_checkpoints = self.env['reached.checkpoint'].search([])
            for rc in reached_checkpoints:
                _logger.info(f"  - {rc.name} (ID: {rc.id})")
            
            # First try exact match with checkpoint names
            checkpoint = task.task_checkpoint_ids.filtered(
                lambda c: checkpoint_name in c.checkpoint_ids.mapped('name')
            )[:1]
            
            if checkpoint:
                _logger.info(f"✅ Found checkpoint by exact name match: {checkpoint.id}")
            
            # If not found, try partial match
            if not checkpoint:
                checkpoint = task.task_checkpoint_ids.filtered(
                    lambda c: any(checkpoint_name.lower() in cp.name.lower() for cp in c.checkpoint_ids)
                )[:1]
                
                if checkpoint:
                    _logger.info(f"✅ Found checkpoint by partial name match: {checkpoint.id}")
            
            # If still not found, try matching by stage or milestone
            if not checkpoint:
                checkpoint = task.task_checkpoint_ids.filtered(
                    lambda c: c.stage_id or c.milestone_id
                )[:1]
                
                if checkpoint:
                    _logger.info(f"✅ Found checkpoint by stage/milestone: {checkpoint.id}")
            
            if not checkpoint:
                _logger.warning(f"No checkpoint found with name '{checkpoint_name}' in task '{task.name}'")
                _logger.info(f"Creating a default checkpoint configuration for task '{task.name}'")
                
                # Create a default checkpoint configuration
                default_checkpoint = self.env['task.checkpoint'].create({
                    'task_id': task.id,
                    'project_id': task.project_id.id if task.project_id else False,
                    'sequence': 10,
                })
                
                # Try to find a suitable stage to move to
                if task.project_id and task.project_id.type_ids:
                    # Get the next stage or use the first available stage
                    current_stage = task.stage_id
                    available_stages = task.project_id.type_ids.sorted('sequence')
                    
                    if current_stage and len(available_stages) > 1:
                        # Find the next stage
                        current_index = available_stages.ids.index(current_stage.id) if current_stage.id in available_stages.ids else -1
                        next_index = min(current_index + 1, len(available_stages) - 1)
                        next_stage = available_stages[next_index]
                        default_checkpoint.stage_id = next_stage.id
                        _logger.info(f"Set default checkpoint stage to: {next_stage.name}")
                    elif available_stages:
                        # Use the first stage
                        default_checkpoint.stage_id = available_stages[0].id
                        _logger.info(f"Set default checkpoint stage to: {available_stages[0].name}")
                
                checkpoint = default_checkpoint
                
            _logger.info(f"Processing checkpoint completion: {checkpoint_name} for task {task.name}")
            
            # Update task stage if configured
            if checkpoint.stage_id:
                _logger.info(f"Updating task stage from '{task.stage_id.name if task.stage_id else 'None'}' to '{checkpoint.stage_id.name}'")
                old_stage = task.stage_id.name if task.stage_id else 'None'
                
                # Force commit any pending changes first
                self.env.cr.commit()
                
                # Update stage with force_write
                task.sudo().with_context(tracking_disable=True).write({
                    'stage_id': checkpoint.stage_id.id,
                })
                
                # Force flush changes
                self.env.cr.flush()
                
                # Clear caches
                self.env.cache.clear()
                task.invalidate_recordset(['stage_id'])
                
                # Reload task to verify stage
                task = task.with_context(prefetch_fields=False).browse(task.id)
                new_stage = task.stage_id.name if task.stage_id else 'None'
                
                _logger.info(f"✅ Stage updated successfully: {old_stage} → {new_stage}")
                
                # Log stage change
                task.message_post(
                    body=f"🔄 **Stage Updated**: Task moved from {old_stage} to {new_stage}",
                    message_type='notification',
                    subtype_xmlid='mail.mt_note'
                )
                
                # Commit changes
                self.env.cr.commit()
            else:
                _logger.warning(f"No stage configured for checkpoint '{checkpoint_name}' in task '{task.name}'")
            
            # Handle milestone if present
            if checkpoint.milestone_id:
                # Trigger milestone notification
                self.trigger_milestone_notification(task, checkpoint.milestone_id)
                
                # Log checkpoint and milestone completion
                task.message_post(
                    body=f"✅ **Checkpoint Completed**: {checkpoint_name}\n\n🎯 Milestone: {checkpoint.milestone_id.name}",
                    message_type='notification'
                )
                
                _logger.info(f"Checkpoint '{checkpoint_name}' completed with milestone '{checkpoint.milestone_id.name}'")
            else:
                # Log just checkpoint completion
                task.message_post(
                    body=f"✅ **Checkpoint Completed**: {checkpoint_name}",
                    message_type='notification'
                )
                
                _logger.info(f"Checkpoint '{checkpoint_name}' completed")
            
            # Clear cache and refresh task
            self.env.cache.clear()
            task.invalidate_recordset()
            
            _logger.info(f"🔄 Task checkpoint completion finished for '{task.name}'")
            
        except Exception as e:
            _logger.error(f"Error completing checkpoint '{checkpoint_name}' for task {task.name}: {e}")
            import traceback
            _logger.error(f"Full traceback: {traceback.format_exc()}")

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