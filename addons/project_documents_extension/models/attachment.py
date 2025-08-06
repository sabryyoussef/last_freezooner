from odoo import models, fields, api
import logging

_logger = logging.getLogger(__name__)

def post_init_hook(cr, registry):
    """Clean up invalid folder_id values when module is installed/upgraded"""
    env = api.Environment(cr, 1, {})
    try:
        # Find all attachments with invalid folder_id
        invalid_attachments = env['ir.attachment'].search([
            ('folder_id', '!=', False)
        ])
        
        # Check which folders actually exist
        existing_folders = env['documents.folder'].search([])
        existing_folder_ids = existing_folders.ids
        
        # Find attachments with non-existent folders
        to_clean = invalid_attachments.filtered(
            lambda att: att.folder_id.id not in existing_folder_ids
        )
        
        if to_clean:
            to_clean.write({'folder_id': False})
            _logger.info(f"Cleaned up {len(to_clean)} attachments with invalid folder_id")
        
    except Exception as e:
        _logger.error(f"Error during folder cleanup: {e}")

class IrAttachmentInherit(models.Model):
    _inherit = 'ir.attachment'

    # Temporarily commented out to prevent AttributeError
    # folder_id = fields.Many2one(
    #     'documents.folder',
    #     string='Folder',
    #     default=False,
    #     help='Select the folder where this document will be stored.'
    # )

    @api.depends('folder_id')
    def _compute_safe_folder_id(self):
        for record in self:
            if record.folder_id and not record.folder_id.exists():
                record.folder_id = False

    @api.onchange('folder_id')
    def _onchange_folder_id(self):
        if self.folder_id and not self.folder_id.exists():
            self.folder_id = False

    def read(self, fields=None, load='_classic_read'):
        # Ensure folder_id is safe before reading
        for record in self:
            if hasattr(record, 'folder_id') and record.folder_id and not record.folder_id.exists():
                record.folder_id = False
        return super().read(fields=fields, load=load)

    def cleanup_invalid_folders(self):
        """Clean up invalid folder_id values in existing records"""
        invalid_attachments = self.search([
            ('folder_id', '!=', False),
            ('folder_id', 'not in', self.env['documents.folder'].search([]).ids)
        ])
        if invalid_attachments:
            invalid_attachments.write({'folder_id': False})
            _logger.info(f"Cleaned up {len(invalid_attachments)} attachments with invalid folder_id")
        return True