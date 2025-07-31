from odoo import api, fields, models

class MilestoneTestWizard(models.TransientModel):
    _name = 'milestone.test.wizard'
    _description = 'Milestone Test Wizard'

    project_id = fields.Many2one('project.project', string='Project', required=True)
    milestone_id = fields.Many2one('project.milestone', string='Milestone')
    checkpoint_name = fields.Char(string='Checkpoint Name')
    action_type = fields.Selection([
        ('progress', 'Get Milestone Progress'),
        ('notification', 'Send Milestone Notification'),
        ('summary', 'Send Milestone Summary Email'),
        ('checkpoint', 'Complete Checkpoint with Milestone')
    ], string='Action Type', required=True, default='progress')

    def action_execute(self):
        """Execute the selected milestone action"""
        self.ensure_one()
        
        if self.action_type == 'progress':
            progress = self.project_id.action_get_milestone_progress()
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Milestone Progress',
                    'message': f"Total: {progress['total']}, Completed: {progress['completed']}, Progress: {progress['percentage']:.1f}%",
                    'type': 'info'
                }
            }
        
        elif self.action_type == 'notification':
            if self.milestone_id:
                self.project_id.action_trigger_milestone_notification(self.milestone_id)
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': 'Milestone Notification',
                        'message': f"Milestone notification sent for {self.milestone_id.name}",
                        'type': 'success'
                    }
                }
        
        elif self.action_type == 'summary':
            self.project_id.action_send_milestone_summary_email()
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Milestone Summary',
                    'message': 'Milestone summary email sent',
                    'type': 'success'
                }
            }
        
        elif self.action_type == 'checkpoint':
            if self.checkpoint_name:
                result = self.project_id.action_complete_checkpoint_with_milestone(self.checkpoint_name)
                if result:
                    return {
                        'type': 'ir.actions.client',
                        'tag': 'display_notification',
                        'params': {
                            'title': 'Checkpoint Completed',
                            'message': f'Checkpoint "{self.checkpoint_name}" completed with milestone notification',
                            'type': 'success'
                        }
                    }
                else:
                    return {
                        'type': 'ir.actions.client',
                        'tag': 'display_notification',
                        'params': {
                            'title': 'Checkpoint Not Found',
                            'message': f'Checkpoint "{self.checkpoint_name}" not found or no milestone linked',
                            'type': 'warning'
                        }
                    }
        
        return {'type': 'ir.actions.act_window_close'} 