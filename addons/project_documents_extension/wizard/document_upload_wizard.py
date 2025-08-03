from odoo import _, api, fields, models
from odoo.exceptions import ValidationError
import logging

_logger = logging.getLogger(__name__)

class DocumentUploadWizard(models.TransientModel):
    _name = 'document.upload.wizard'
    _description = 'Document Upload Wizard'

    project_id = fields.Many2one('project.project', string='Project', required=True)
    user_id = fields.Many2one('res.users', string='User', required=True)
    name = fields.Char('Document Name', required=True)
    document_type = fields.Selection([
        ('required', 'Required Document'),
        ('deliverable', 'Deliverable Document')
    ], string='Document Type', required=True)
    comment = fields.Text('Comment')
    document_line_id = fields.Integer('Document Line ID')
    attachment = fields.Binary('File', required=True, help='Select the file to upload')
    attachment_filename = fields.Char('File Name')
    
    # Additional fields from documents.document form
    folder_id = fields.Many2one('documents.document', string='Folder', domain="[('type', '=', 'folder')]")
    contact_id = fields.Many2one('res.partner', string='Contact')
    tag_ids = fields.Many2many('documents.tag', string='Tags')
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company)
    file_size = fields.Integer('File Size', readonly=True)
    mimetype = fields.Char('Mime Type', readonly=True)
    create_activity = fields.Boolean('Create a new activity', default=False)
    number = fields.Char('Number', default='New')
    is_verified = fields.Boolean('Is Verified', default=False)
    
    @api.onchange('attachment')
    def _onchange_attachment(self):
        """Update file size and mimetype when attachment changes"""
        if self.attachment:
            # Calculate file size (approximate)
            import base64
            try:
                file_data = base64.b64decode(self.attachment)
                self.file_size = len(file_data)
                
                # Try to determine mimetype from filename
                if self.attachment_filename:
                    import mimetypes
                    self.mimetype = mimetypes.guess_type(self.attachment_filename)[0] or 'application/octet-stream'
                else:
                    self.mimetype = 'application/octet-stream'
                    
                _logger.info(f"📄 File uploaded: {self.attachment_filename}, size: {self.file_size} bytes, type: {self.mimetype}")
            except Exception as e:
                _logger.error(f"❌ Error processing attachment: {e}")
                self.file_size = 0
                self.mimetype = 'application/octet-stream'

    def action_upload(self):
        _logger.info("🚀 WIZARD ACTION_UPLOAD CALLED")
        for rec in self:
            _logger.info(f"🔄 Starting upload for document: {rec.name}")
            
            # Create attachment first
            attachment_vals = {
                'name': rec.attachment_filename or rec.name,
                'datas': rec.attachment,
                'res_model': 'project.project',
                'res_id': rec.project_id.id,
            }
            
            attachment = self.env['ir.attachment'].create(attachment_vals)
            _logger.info(f"✅ Created attachment: {attachment.name}")
            
            # Get the documents folder for the project
            folder_id = False
            try:
                # Check if documents module is available
                if 'documents.document' not in self.env:
                    _logger.warning("Documents module not available")
                    _logger.info("🚪 RETURNING WINDOW CLOSE - NO DOCUMENTS MODULE")
                    return {'type': 'ir.actions.act_window_close'}
                
                # Ensure project has a documents folder
                rec.project_id._ensure_project_folder()
                folder_id = rec.project_id.documents_folder_id.id if rec.project_id.documents_folder_id else False
            except Exception as e:
                _logger.warning(f"Could not create documents folder for project {rec.project_id.name}: {e}")
            
            # Create the document with attachment
            try:
                document_vals = {
                    'name': rec.name,
                    'user_id': rec.user_id.id,
                    'res_model': 'project.project',
                    'res_id': rec.project_id.id,
                    'type': 'file',
                    'attachment_id': attachment.id,  # Link the attachment
                    'contact_id': rec.contact_id.id if rec.contact_id else False,
                    'tag_ids': [(6, 0, rec.tag_ids.ids)] if rec.tag_ids else False,
                    'company_id': rec.company_id.id if rec.company_id else False,
                    'number': rec.number,
                    'is_verified': rec.is_verified,
                }
                
                # Use selected folder or project folder
                if rec.folder_id:
                    document_vals['folder_id'] = rec.folder_id.id
                    _logger.info(f"📁 Using selected folder: {rec.folder_id.name}")
                elif folder_id:
                    document_vals['folder_id'] = folder_id
                    _logger.info(f"📁 Using project folder: {folder_id}")
                else:
                    _logger.warning(f"⚠️ No folder selected for project '{rec.project_id.name}'")
                
                # Create the document
                document = self.env['documents.document'].create(document_vals)
                _logger.info(f"✅ Created document '{rec.name}' with ID {document.id}")
                
                # Update the document line with the created document (using new x_ models)
                if rec.document_line_id:
                    # Try deliverable document first
                    document_line = self.env['project.deliverable.document'].browse(rec.document_line_id)
                    if document_line.exists():
                        document_line.write({'document_id': document.id})
                        _logger.info(f"✅ Updated deliverable document line {rec.document_line_id} with document {document.id}")
                    else:
                        # Try required document line
                        document_line = self.env['project.required.document'].browse(rec.document_line_id)
                        if document_line.exists():
                            document_line.write({'document_id': document.id})
                            _logger.info(f"✅ Updated required document line {rec.document_line_id} with document {document.id}")
                        else:
                            _logger.warning(f"⚠️ Could not find document line with ID {rec.document_line_id}")
                
                # Post message to project chatter
                body = _(
                    "<b>Document Uploaded.</b><br/>"
                    "<b>Document:</b> %(doc_name)s<br/>"
                    "<b>Type:</b> %(doc_type)s<br/>"
                    "<b>Uploaded by:</b> %(user_name)s<br/>"
                    "<b>Comment:</b> %(comment)s<br/><br/>"
                ) % {
                    "doc_name": rec.name,
                    "doc_type": dict(rec._fields['document_type'].selection).get(rec.document_type, rec.document_type),
                    "user_name": rec.user_id.name,
                    "comment": rec.comment or "No comment",
                }
                
                rec.project_id.message_post(
                    body=body,
                    message_type="comment",
                    subtype_xmlid="mail.mt_note",
                )
                
                _logger.info(f"✅ Successfully uploaded document '{rec.name}' for project '{rec.project_id.name}'")
                
                # Close wizard without opening another window
                _logger.info("🚪 RETURNING WINDOW CLOSE - SUCCESS")
                return {'type': 'ir.actions.act_window_close'}
                
            except Exception as e:
                _logger.error(f"❌ Failed to create document: {e}")
                # Clean up attachment if document creation failed
                if attachment.exists():
                    attachment.unlink()
                
                _logger.info("🚪 RETURNING WINDOW CLOSE - ERROR")
                return {'type': 'ir.actions.act_window_close'} 