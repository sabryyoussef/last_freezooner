from odoo import models, fields, api
import logging

_logger = logging.getLogger(__name__)

class ProjectTask(models.Model):
    _inherit = 'project.task'
    
    def action_complete_required_documents(self):
        """Complete required documents and trigger checkpoint"""
        _logger.info(f"🔧 Completing required documents for task {self.name}")
        checkpoint_service = self.env['task.checkpoint.service']
        checkpoint_service.handle_document_completion(self, 'complete')
        return True
        
    def action_confirm_required_documents(self):
        """Confirm required documents and trigger checkpoint"""
        _logger.info(f"🔧 Confirming required documents for task {self.name}")
        checkpoint_service = self.env['task.checkpoint.service']
        checkpoint_service.handle_document_completion(self, 'confirm')
        return True
