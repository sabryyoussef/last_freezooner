from odoo import api, fields, models

class ProjectMilestone(models.Model):
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