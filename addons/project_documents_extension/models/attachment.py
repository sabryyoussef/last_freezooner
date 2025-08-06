from odoo import models, fields, api
import logging

_logger = logging.getLogger(__name__)

class IrAttachmentInherit(models.Model):
    _inherit = 'ir.attachment'

    folder_id = fields.Many2one(
        'documents.folder',
        string='Folder',
        default=lambda self: self._get_default_project_folder(),
        help='Select the folder where this document will be stored.',
        ondelete='set null'  # Set to null if folder is deleted
    )

    @api.model
    def _get_default_project_folder(self):
        """Get default project folder based on context"""
        try:
            # Check if we're in a project context
            project_id = self.env.context.get('default_project_id') or self.env.context.get('project_id')
            if project_id:
                project = self.env['project.project'].browse(project_id)
                if project.exists():
                    # Try to find or create project folder
                    project_folder = self._get_or_create_project_folder(project)
                    if project_folder:
                        return project_folder.id
            
            # If no project context, try to get from res_model and res_id
            res_model = self.env.context.get('default_res_model')
            res_id = self.env.context.get('default_res_id')
            
            if res_model == 'project.project' and res_id:
                project = self.env['project.project'].browse(res_id)
                if project.exists():
                    project_folder = self._get_or_create_project_folder(project)
                    if project_folder:
                        return project_folder.id
            
            return False
            
        except Exception as e:
            _logger.error(f"Error getting default project folder: {e}")
            return False

    @api.model
    def _get_or_create_project_folder(self, project):
        """Get or create project folder"""
        try:
            # First try to find existing project folder
            project_folder = self.env['documents.folder'].search([
                ('name', '=', f'Project: {project.name}'),
                ('company_id', '=', project.company_id.id)
            ], limit=1)
            
            if project_folder:
                return project_folder
            
            # If not found, create new project folder
            project_folder = self.env['documents.folder'].create({
                'name': f'Project: {project.name}',
                'company_id': project.company_id.id,
                'description': f'Documents for project: {project.name}'
            })
            
            _logger.info(f"Created project folder: {project_folder.name}")
            return project_folder
            
        except Exception as e:
            _logger.error(f"Error creating project folder: {e}")
            return False

    @api.depends('folder_id')
    def _compute_safe_folder_id(self):
        for record in self:
            if record.folder_id and not record.folder_id.exists():
                record.folder_id = False

    @api.onchange('folder_id')
    def _onchange_folder_id(self):
        if self.folder_id and not self.folder_id.exists():
            self.folder_id = False

    @api.model
    def create(self, vals):
        """Override create to handle folder_id safely"""
        if 'folder_id' in vals and vals['folder_id']:
            # Check if the folder exists
            try:
                folder = self.env['documents.folder'].browse(vals['folder_id'])
                if not folder.exists():
                    vals['folder_id'] = False
                    _logger.warning(f"Attempted to create with invalid folder_id: {vals['folder_id']}")
            except Exception as e:
                vals['folder_id'] = False
                _logger.error(f"Error checking folder_id during create: {e}")
        
        return super().create(vals)

    def write(self, vals):
        """Override write to handle folder_id safely"""
        if 'folder_id' in vals and vals['folder_id']:
            # Check if the folder exists
            try:
                folder = self.env['documents.folder'].browse(vals['folder_id'])
                if not folder.exists():
                    vals['folder_id'] = False
                    _logger.warning(f"Attempted to set invalid folder_id: {vals['folder_id']}")
            except Exception as e:
                vals['folder_id'] = False
                _logger.error(f"Error checking folder_id: {e}")
        
        return super().write(vals)

    def read(self, fields=None, load='_classic_read'):
        # First, clean up any invalid folder_id values in the database
        try:
            # Get existing folders
            existing_folders = self.env['documents.folder'].search([])
            existing_folder_ids = existing_folders.ids
            
            # Find attachments with invalid folder_id and fix them
            invalid_attachments = self.search([
                ('folder_id', '!=', False),
                ('folder_id', 'not in', existing_folder_ids)
            ])
            
            if invalid_attachments:
                invalid_attachments.write({'folder_id': False})
                _logger.info(f"Cleaned up {len(invalid_attachments)} attachments with invalid folder_id during read")
                
        except Exception as e:
            _logger.error(f"Error during read cleanup: {e}")
        
        # Now read the data safely
        try:
            result = super().read(fields=fields, load=load)
            
            # Additional safety check for the result
            if isinstance(result, list):
                for record in result:
                    if 'folder_id' in record and record['folder_id']:
                        # Check if the folder_id is a valid ID
                        try:
                            folder = self.env['documents.folder'].browse(record['folder_id'])
                            if not folder.exists():
                                record['folder_id'] = False
                        except:
                            record['folder_id'] = False
            
            return result
            
        except Exception as e:
            _logger.error(f"Error in read method: {e}")
            # Fallback: try to read without folder_id field
            if fields and 'folder_id' in fields:
                safe_fields = [f for f in fields if f != 'folder_id']
                if safe_fields:
                    try:
                        result = super().read(fields=safe_fields, load=load)
                        # Add folder_id as False for all records
                        for record in result:
                            record['folder_id'] = False
                        return result
                    except Exception as fallback_error:
                        _logger.error(f"Fallback read also failed: {fallback_error}")
            # If all else fails, return empty result
            return []

    def search(self, domain, offset=0, limit=None, order=None, count=False):
        """Override search to handle _unknown records safely"""
        try:
            # Handle count parameter separately
            if count:
                return super().search(domain, offset=offset, limit=limit, order=order).count()
            else:
                return super().search(domain, offset=offset, limit=limit, order=order)
        except Exception as e:
            _logger.error(f"Error in search method: {e}")
            # If there's an error, try to clean up invalid records first
            try:
                # Clean up any invalid folder_id values
                invalid_attachments = self.search([
                    ('folder_id', '!=', False),
                    ('folder_id', 'not in', self.env['documents.folder'].search([]).ids)
                ])
                if invalid_attachments:
                    invalid_attachments.write({'folder_id': False})
                    _logger.info(f"Cleaned up {len(invalid_attachments)} attachments during search error")
            except:
                pass
            
            # Try the search again
            if count:
                return super().search(domain, offset=offset, limit=limit, order=order).count()
            else:
                return super().search(domain, offset=offset, limit=limit, order=order)

    def browse(self, ids=None):
        """Override browse to handle _unknown records safely"""
        try:
            return super().browse(ids)
        except Exception as e:
            _logger.error(f"Error in browse method: {e}")
            # If there's an error, try to clean up invalid records first
            try:
                # Clean up any invalid folder_id values
                invalid_attachments = self.search([
                    ('folder_id', '!=', False),
                    ('folder_id', 'not in', self.env['documents.folder'].search([]).ids)
                ])
                if invalid_attachments:
                    invalid_attachments.write({'folder_id': False})
                    _logger.info(f"Cleaned up {len(invalid_attachments)} attachments during browse error")
            except:
                pass
            
            # Try the browse again
            return super().browse(ids)

    def cleanup_invalid_folders(self):
        """Clean up invalid folder_id values in existing records"""
        try:
            invalid_attachments = self.search([
                ('folder_id', '!=', False),
                ('folder_id', 'not in', self.env['documents.folder'].search([]).ids)
            ])
            if invalid_attachments:
                invalid_attachments.write({'folder_id': False})
                _logger.info(f"Cleaned up {len(invalid_attachments)} attachments with invalid folder_id")
        except Exception as e:
            _logger.error(f"Error in cleanup_invalid_folders: {e}")
        return True

    def _get_folder_id_domain(self):
        """Get domain for valid folders only"""
        try:
            existing_folders = self.env['documents.folder'].search([])
            return [('id', 'in', existing_folders.ids)]
        except:
            return [('id', '=', False)]

    @api.model
    def _get_context_for_folder_selection(self):
        """Get context for folder selection with valid folders only"""
        try:
            existing_folders = self.env['documents.folder'].search([])
            return {'valid_folder_ids': existing_folders.ids}
        except:
            return {'valid_folder_ids': []}

    @api.model
    def _cleanup_all_invalid_folders(self):
        """Clean up all invalid folder_id values in the database"""
        try:
            # Get all attachments with folder_id
            all_attachments = self.search([('folder_id', '!=', False)])
            
            # Get existing folders
            existing_folders = self.env['documents.folder'].search([])
            existing_folder_ids = existing_folders.ids
            
            # Find and fix invalid folder_id values
            invalid_attachments = all_attachments.filtered(
                lambda att: att.folder_id.id not in existing_folder_ids
            )
            
            if invalid_attachments:
                invalid_attachments.write({'folder_id': False})
                _logger.info(f"Cleaned up {len(invalid_attachments)} attachments with invalid folder_id")
                return len(invalid_attachments)
            else:
                _logger.info("No invalid folder_id values found")
                return 0
                
        except Exception as e:
            _logger.error(f"Error in _cleanup_all_invalid_folders: {e}")
            return 0

    @api.model
    def _safe_get_attachments(self, domain=None):
        """Safely get attachments with error handling"""
        try:
            if domain is None:
                domain = []
            return self.search(domain)
        except Exception as e:
            _logger.error(f"Error in _safe_get_attachments: {e}")
            # Try to clean up and retry
            try:
                self._cleanup_all_invalid_folders()
                return self.search(domain)
            except:
                return self.env['ir.attachment']