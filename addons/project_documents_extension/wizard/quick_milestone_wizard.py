from odoo import api, fields, models

class QuickMilestoneWizard(models.TransientModel):
    _name = 'quick.milestone.wizard'
    _description = 'Quick Milestone Creation Wizard'

    project_id = fields.Many2one('project.project', string='Project', required=True)
    name = fields.Char(string='Milestone Name', required=True)
    deadline = fields.Date(string='Deadline')
    milestone_message = fields.Text(string='Milestone Message')
    mail_template_id = fields.Many2one('mail.template', string='Email Template')

    @api.model
    def default_get(self, fields_list):
        """Set default values"""
        res = super().default_get(fields_list)
        if self.env.context.get('default_project_id'):
            res['project_id'] = self.env.context.get('default_project_id')
        return res

    def action_create_milestone(self):
        """Create the milestone"""
        self.ensure_one()
        
        # Create the milestone
        milestone_vals = {
            'name': self.name,
            'project_id': self.project_id.id,
            'deadline': self.deadline,
            'milestone_message': self.milestone_message,
            'mail_template_id': self.mail_template_id.id if self.mail_template_id else False,
        }
        
        milestone = self.env['project.milestone'].create(milestone_vals)
        
        # Post message to project
        self.project_id.message_post(
            body=f"🎯 **New Milestone Created**: {milestone.name}\n\n{milestone.milestone_message or 'Milestone created successfully.'}",
            message_type='notification'
        )
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Milestone Created',
                'message': f'Milestone "{milestone.name}" has been created successfully!',
                'type': 'success'
            }
        } 