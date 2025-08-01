from odoo import models, fields, api

class DuplicateDocumentWarningWizard(models.TransientModel):
    _name = 'duplicate.document.warning.wizard'
    _description = 'Duplicate Document Warning Wizard'

    message = fields.Text(string='Warning Message', readonly=True)

    def action_close(self):
        """Close the wizard"""
        return {'type': 'ir.actions.act_window_close'} 