from odoo import models, fields, api, _
from odoo.exceptions import UserError
import logging

_logger = logging.getLogger(__name__)


class DocumentActionConfirmationWizard(models.TransientModel):
    _name = 'document.action.confirmation.wizard'
    _description = 'Document Action Confirmation Wizard'

    title = fields.Char(string='Title', required=True)
    message = fields.Text(string='Message', required=True)
    action_type = fields.Selection([
        ('repeat_required', 'Repeat Required Documents'),
        ('return_required', 'Return Required Documents'),
        ('repeat_deliverable', 'Repeat Deliverable Documents'),
        ('return_deliverable', 'Return Deliverable Documents'),
        ('project_return', 'Project Return'),
        ('project_update', 'Project Update'),
    ], string='Action Type', required=True)
    record_id = fields.Integer(string='Record ID', required=True)
    record_model = fields.Char(string='Record Model', required=True)

    def action_confirm(self):
        """Execute the confirmed action"""
        self.ensure_one()
        
        # Get the record
        record = self.env[self.record_model].browse(self.record_id)
        if not record.exists():
            raise UserError(_("Record not found."))
        
        # Execute the appropriate action based on action_type
        if self.action_type == 'repeat_required':
            return record._execute_repeat_required_documents()
        elif self.action_type == 'return_required':
            return record._execute_return_required_documents()
        elif self.action_type == 'repeat_deliverable':
            return record._execute_repeat_deliverable_documents()
        elif self.action_type == 'return_deliverable':
            return record._execute_return_deliverable_documents()
        elif self.action_type == 'project_return':
            return record._execute_project_return()
        elif self.action_type == 'project_update':
            return record._execute_project_update()
        
        return {'type': 'ir.actions.act_window_close'}

    def action_cancel(self):
        """Cancel the action"""
        return {'type': 'ir.actions.act_window_close'} 