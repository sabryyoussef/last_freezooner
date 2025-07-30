# -*- coding: utf-8 -*-

import logging
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
from collections import defaultdict

_logger = logging.getLogger(__name__)


# OLD FUNCTION - REPLACED BY DOCUMENT SERVICE
# def copy_documents_from_product_to_project(env, project, product_templates):
#     """This function has been replaced by the Document Service pattern"""
#     pass


def copy_documents_from_project_to_task(env, task, project):
    """Copy document types from project to task"""
    # Copy required documents if they exist
    if hasattr(project, 'document_required_type_ids') and project.document_required_type_ids:
        for req_doc in project.document_required_type_ids:
            env['project.document.required.line'].create({
                'task_id': task.id,
                'document_type_id': req_doc.document_type_id.id,
                'is_required': req_doc.is_required,
            })
    # Copy deliverable documents if they exist
    if hasattr(project, 'document_type_ids') and project.document_type_ids:
        for del_doc in project.document_type_ids:
            env['project.document.type.line'].create({
                'task_id': task.id,
                'document_type_id': del_doc.document_type_id.id,
                'is_required': del_doc.is_required,
            })

def copy_checkpoints_from_template_to_task(env, task, template):
    """Copy checkpoint configurations from product task template to task"""
    if hasattr(template, 'checkpoint_ids') and template.checkpoint_ids:
        for checkpoint_config in template.checkpoint_ids:
            env['task.checkpoint'].create({
                'task_id': task.id,
                'checkpoint_ids': [(6, 0, checkpoint_config.checkpoint_ids.ids)],
                'stage_id': checkpoint_config.stage_id.id if checkpoint_config.stage_id else False,
                'milestone_id': checkpoint_config.milestone_id.id if checkpoint_config.milestone_id else False,
                'sequence': checkpoint_config.sequence,
            })


class ProjectDocumentCategory(models.Model):
    _name = 'project.document.category'
    _description = 'Project Document Category'
    _rec_name = 'name'

    name = fields.Char('Category Name', required=True)
    description = fields.Text('Description')
    document_type_ids = fields.One2many('project.document.type', 'category_id', string='Document Types')


class ProjectDocumentType(models.Model):
    _name = 'project.document.type'
    _description = 'Project Document Type'

    name = fields.Char('Type Name', required=True)
    category_id = fields.Many2one('project.document.category', string='Category')
    description = fields.Text('Description')
    is_required = fields.Boolean('Required', default=False)
    expiry_required = fields.Boolean('Expiry Required', default=False)
    reminder_days = fields.Integer('Reminder Days', default=30, help='Days before expiry to send reminder')
    document_ids = fields.One2many('project.document.type.line', 'document_type_id', string='Document Lines')


class ProjectDocumentTypeLine(models.Model):
    _name = 'project.document.type.line'
    _description = 'Project Deliverable Document Type Line'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    project_id = fields.Many2one('project.project', string='Project', ondelete='cascade')
    task_id = fields.Many2one('project.task', string='Task', ondelete='cascade')
    product_tmpl_id = fields.Many2one('product.template', string='Product Template', ondelete='cascade')
    document_type_id = fields.Many2one('project.document.type', string='Document Type', required=True)
    document_id = fields.Many2one('documents.document', string='Document', required=False)
    is_required = fields.Boolean(string='Required', default=False)
    expiry_date = fields.Date('Expiry Date')
    reminder_days = fields.Integer('Reminder Days', default=30)
    is_expired = fields.Boolean('Is Expired', default=False)
    is_verify = fields.Boolean('Is Verified', default=False)
    number = fields.Char(
        string="Number",
        required=True,
        copy=False,
        readonly=True,
        index=True,
        default=lambda self: _("New"),
    )
    issue_date = fields.Date(
        default=fields.Date.today,
        help="Date when the document was issued",
    )
    attachment_ids = fields.Many2many('ir.attachment', string='Attachments')
    expiration_reminder = fields.Boolean(default=False)
    expiration_reminder_sent = fields.Boolean(default=False)
    document_create_date = fields.Datetime(
        readonly=True,
        string="Document Create Date",
        default=fields.datetime.now(),
    )

    @api.depends('expiry_date')
    def _compute_expired(self):
        """Compute document expiry status with smooth error handling"""
        try:
            today = fields.Date.today()
            _logger.info(f"Computing expiry status for {len(self)} documents")
            for record in self:
                try:
                    if record.expiry_date:
                        is_expired = record.expiry_date < today
                        record.is_expired = is_expired
                        if is_expired:
                            _logger.warning(f"Document {record.id} ({getattr(record, 'document_type_id', False) and record.document_type_id.name or 'Unknown'}) is EXPIRED (expiry: {record.expiry_date})")
                        else:
                            _logger.info(f"Document {record.id} ({getattr(record, 'document_type_id', False) and record.document_type_id.name or 'Unknown'}) is VALID (expiry: {record.expiry_date})")
                    else:
                        record.is_expired = False
                        _logger.debug(f"Document {record.id} has no expiry date set")
                except Exception as e:
                    _logger.error(f"Error computing expiry for document {record.id}: {str(e)}")
                    record.is_expired = False
        except Exception as e:
            _logger.error(f"Error in document expiry computation: {str(e)}")
            for record in self:
                record.is_expired = False

    def action_numbers(self):
        docs = self.env['project.document.type.line'].sudo().search([])
        for doc in docs:
            doc.number = self.env['ir.sequence'].next_by_code('project.document.type.line') or _("New")

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if 'number' not in vals:
                vals['number'] = self.env['ir.sequence'].next_by_code('project.document.type.line') or _("New")
        records = super(ProjectDocumentTypeLine, self).create(vals_list)
        
        # Check for duplicates after creation
        for record in records:
            record._check_duplicate_after_create()
        
        return records

    def _check_duplicate_after_create(self):
        """Check for duplicates after document creation"""
        _logger.info(f"Checking for duplicates after create for required document {self.id}")
        
        try:
            # Build domain to find potential duplicates
            domain = [
                ('document_type_id', '=', self.document_type_id.id),
                ('id', '!=', self.id)
            ]
            
            # Add context-specific conditions
            if self.project_id:
                domain.append(('project_id', '=', self.project_id.id))
                context_info = f" in project {self.project_id.name}"
            elif self.task_id:
                domain.append(('task_id', '=', self.task_id.id))
                context_info = f" in task {self.task_id.name}"
            elif self.product_tmpl_id:
                domain.append(('product_tmpl_id', '=', self.product_tmpl_id.id))
                context_info = f" in product {self.product_tmpl_id.name}"
            else:
                context_info = ""
            
            duplicate_documents = self.search(domain)
            _logger.info(f"Found {len(duplicate_documents)} potential duplicates for required document {self.id}")
            
            if duplicate_documents:
                _logger.info(f"Duplicate required documents found: {duplicate_documents.ids}")
                
                for duplicate in duplicate_documents:
                    # Check if attachments are the same
                    if self.attachment_ids and duplicate.attachment_ids:
                        self_attachment_ids = set(self.attachment_ids.mapped('id'))
                        dup_attachment_ids = set(duplicate.attachment_ids.mapped('id'))
                        
                        if self_attachment_ids == dup_attachment_ids and self_attachment_ids:
                            _logger.info(f"Duplicate required document detected with same attachments: {self.id} vs {duplicate.id}")
                            
                            # Post warning to project chatter
                            if self.project_id:
                                self.project_id.message_post(
                                    body=_("⚠️ Duplicate required document detected: %s with same attachments as existing document%s") % (
                                        self.document_type_id.name, context_info
                                    )
                                )
                            
                            # Prevent saving by raising ValidationError
                            raise ValidationError(_("⚠️ Duplicate required document detected: %s with same attachments as existing document%s") % (
                                self.document_type_id.name, context_info
                            ))
                    else:
                        # If no attachments, check for same document type in same context
                        _logger.info(f"Duplicate required document detected (same document type): {self.id} vs {duplicate.id}")
                        
                        # Post warning to project chatter
                        if self.project_id:
                            self.project_id.message_post(
                                body=_("⚠️ Duplicate required document detected: %s (same document type)%s") % (
                                    self.document_type_id.name, context_info
                                )
                            )
                        
                        # Prevent saving by raising ValidationError
                        raise ValidationError(_("⚠️ Duplicate required document detected: %s (same document type)%s") % (
                            self.document_type_id.name, context_info
                        ))
                        
        except ValidationError:
            # Re-raise ValidationError to prevent saving
            raise
        except Exception as e:
            _logger.error(f"Error checking duplicate after create for required document {self.id}: {str(e)}")
            import traceback
            _logger.error(f"Full traceback: {traceback.format_exc()}")

    @api.constrains('project_id', 'task_id', 'product_tmpl_id', 'document_type_id')
    def check_duplicate_document(self):
        """Check for duplicate documents - SIMPLIFIED VERSION"""
        for record in self:
            if not record.document_type_id:
                continue
                
            # Build domain based on context
            domain = [
                ('document_type_id', '=', record.document_type_id.id),
                ('id', '!=', record.id)
            ]
            
            # Add context-specific filter
            if record.product_tmpl_id:
                domain.append(('product_tmpl_id', '=', record.product_tmpl_id.id))
                context_name = record.product_tmpl_id.name
            elif record.project_id:
                domain.append(('project_id', '=', record.project_id.id))
                context_name = record.project_id.name
            elif record.task_id:
                domain.append(('task_id', '=', record.task_id.id))
                context_name = record.task_id.name
            else:
                continue  # Skip if no context
            
            # Check for duplicates
            duplicates = self.search(domain)
            if duplicates:
                raise ValidationError(_(
                    "⚠️ Duplicate document detected: '%s' already exists in '%s'"
                ) % (record.document_type_id.name, context_name))

    def write(self, vals):
        res = super(ProjectDocumentTypeLine, self).write(vals)
        if vals.get('expiry_date'):
            self.write({'expiration_reminder_sent': False})
        if vals.get('attachment_ids'):
            self.write({'document_create_date': fields.Datetime.today()})
        return res

    def action_upload_document(self):
        """Action to upload document for this line"""
        self.ensure_one()
        return {
            'name': _('Upload Document'),
            'type': 'ir.actions.act_window',
            'res_model': 'document.upload.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_name': self.document_type_id.name,
                'default_document_type': 'deliverable' if self.project_id else 'required',
                'default_project_id': self.project_id.id if self.project_id else False,
                'default_task_id': self.task_id.id if self.task_id else False,
                'default_document_line_id': self.id,
            }
        }

    def _trigger_duplicate_popup(self, message):
        """Trigger a popup notification for duplicate detection"""
        try:
            # Set context flag for notification
            self.env.context = dict(self.env.context, 
                duplicate_warning=True, 
                duplicate_message=message,
                duplicate_title=_('Duplicate Document Detected')
            )
            
            # Log the notification
            _logger.info(f"Duplicate popup triggered: {message}")
            
            return True
            
        except Exception as e:
            _logger.error(f"Error triggering duplicate popup: {str(e)}")
            return False


class ProjectDocumentRequiredLine(models.Model):
    _name = 'project.document.required.line'
    _description = 'Project Required Document Type Line'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    project_id = fields.Many2one('project.project', string='Project', ondelete='cascade')
    task_id = fields.Many2one('project.task', string='Task', ondelete='cascade')
    product_tmpl_id = fields.Many2one('product.template', string='Product Template', ondelete='cascade')
    document_type_id = fields.Many2one('project.document.type', string='Document Type', required=True)
    document_id = fields.Many2one('documents.document', string='Document', required=False)
    is_required = fields.Boolean(string='Required', default=False)
    expiry_date = fields.Date('Expiry Date')
    reminder_days = fields.Integer('Reminder Days', default=30)
    is_expired = fields.Boolean('Is Expired', default=False)
    is_verify = fields.Boolean('Is Verified', default=False)
    number = fields.Char(
        string="Number",
        required=True,
        copy=False,
        readonly=True,
        index=True,
        default=lambda self: _("New"),
    )
    issue_date = fields.Date(
        default=fields.Date.today,
        help="Date when the document was issued",
    )
    attachment_ids = fields.Many2many('ir.attachment', string='Attachments')
    expiration_reminder = fields.Boolean(default=False)
    expiration_reminder_sent = fields.Boolean(default=False)
    document_create_date = fields.Datetime(
        readonly=True,
        string="Document Create Date",
        default=fields.datetime.now(),
    )

    @api.depends('expiry_date')
    def _compute_expired(self):
        """Compute document expiry status with smooth error handling"""
        try:
            today = fields.Date.today()
            _logger.info(f"Computing expiry status for {len(self)} required documents")
            for record in self:
                try:
                    if record.expiry_date:
                        is_expired = record.expiry_date < today
                        record.is_expired = is_expired
                        if is_expired:
                            _logger.warning(f"Required Document {record.id} ({getattr(record, 'document_type_id', False) and record.document_type_id.name or 'Unknown'}) is EXPIRED (expiry: {record.expiry_date})")
                        else:
                            _logger.info(f"Required Document {record.id} ({getattr(record, 'document_type_id', False) and record.document_type_id.name or 'Unknown'}) is VALID (expiry: {record.expiry_date})")
                    else:
                        record.is_expired = False
                        _logger.debug(f"Required Document {record.id} has no expiry date set")
                except Exception as e:
                    _logger.error(f"Error computing expiry for required document {record.id}: {str(e)}")
                    record.is_expired = False
        except Exception as e:
            _logger.error(f"Error in required document expiry computation: {str(e)}")
            for record in self:
                record.is_expired = False

    def action_numbers(self):
        docs = self.env['project.document.required.line'].sudo().search([])
        for doc in docs:
            doc.number = self.env['ir.sequence'].next_by_code('project.document.required.line') or _("New")

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if 'number' not in vals:
                vals['number'] = self.env['ir.sequence'].next_by_code('project.document.required.line') or _("New")
        records = super(ProjectDocumentRequiredLine, self).create(vals_list)
        
        # Check for duplicates after creation
        for record in records:
            record._check_duplicate_after_create()
        
        return records

    def _check_duplicate_after_create(self):
        """Check for duplicates after document creation"""
        _logger.info(f"🔍 DEBUG: _check_duplicate_after_create called for required document {self.id}")
        _logger.info(f"🔍 DEBUG: Document type: {self.document_type_id.name if self.document_type_id else 'None'}")
        _logger.info(f"🔍 DEBUG: Product template: {self.product_tmpl_id.name if self.product_tmpl_id else 'None'}")
        _logger.info(f"🔍 DEBUG: Project: {self.project_id.name if self.project_id else 'None'}")
        _logger.info(f"🔍 DEBUG: Attachments: {len(self.attachment_ids)}")
        
        try:
            # Build domain for duplicate check - check multiple criteria
            domain = [
                ('document_type_id', '=', self.document_type_id.id),
                ('id', '!=', self.id),
            ]
            
            # Add project/task/product filters
            if self.project_id:
                domain.append(('project_id', '=', self.project_id.id))
            if self.task_id:
                domain.append(('task_id', '=', self.task_id.id))
            if self.product_tmpl_id:
                domain.append(('product_tmpl_id', '=', self.product_tmpl_id.id))
            
            _logger.info(f"🔍 DEBUG: Search domain: {domain}")
            
            # Search for duplicates with same document type and project/task/product
            duplicate_documents = self.search(domain)
            _logger.info(f"🔍 DEBUG: Found {len(duplicate_documents)} potential duplicates")
            
            if duplicate_documents:
                _logger.info(f"🔍 DEBUG: Checking {len(duplicate_documents)} duplicates for attachments")
                # Check if any duplicates have the same attachments
                for duplicate in duplicate_documents:
                    _logger.info(f"🔍 DEBUG: Checking duplicate {duplicate.id} with {len(duplicate.attachment_ids)} attachments")
                    if self.attachment_ids and duplicate.attachment_ids:
                        # Check if attachments are the same
                        self_attachment_ids = set(self.attachment_ids.ids)
                        dup_attachment_ids = set(duplicate.attachment_ids.ids)
                        
                        _logger.info(f"🔍 DEBUG: Self attachments: {self_attachment_ids}")
                        _logger.info(f"🔍 DEBUG: Duplicate attachments: {dup_attachment_ids}")
                        
                        if self_attachment_ids == dup_attachment_ids and self_attachment_ids:
                            context_info = ""
                            if self.product_tmpl_id:
                                context_info = f" in product {self.product_tmpl_id.name}"
                            elif self.project_id:
                                context_info = f" in project {self.project_id.name}"
                            
                            _logger.warning(f"Duplicate required document detected for {self.document_type_id.name} with same attachments{context_info}")
                            # Post warning message to project chatter
                            if self.project_id:
                                self.project_id.message_post(
                                    body=_("🚨 POPUP_WARNING: Duplicate required document detected: %s with same attachments as existing document%s") % (
                                        self.document_type_id.name, context_info
                                    )
                                )
                            # Trigger popup notification
                            self._trigger_duplicate_popup(_('🚨 POPUP_WARNING: Duplicate required document detected: %s with same attachments as existing document%s') % (
                                self.document_type_id.name, context_info
                            ))
                            break
                    else:
                        # If no attachments, check for same document type in same context
                        context_info = ""
                        if self.product_tmpl_id:
                            context_info = f" in product {self.product_tmpl_id.name}"
                        elif self.project_id:
                            context_info = f" in project {self.project_id.name}"
                        
                        _logger.warning(f"Duplicate required document detected for {self.document_type_id.name} (same type){context_info}")
                        # Post warning message to project chatter
                        if self.project_id:
                            self.project_id.message_post(
                                body=_("🚨 POPUP_WARNING: Duplicate required document detected: %s (same document type)%s") % (
                                    self.document_type_id.name, context_info
                                )
                            )
                        # Trigger popup notification
                        self._trigger_duplicate_popup(_('🚨 POPUP_WARNING: Duplicate required document detected: %s (same document type)%s') % (
                            self.document_type_id.name, context_info
                        ))
                        break
            else:
                _logger.info(f"🔍 DEBUG: No duplicates found")
                    
        except Exception as e:
            _logger.error(f"Error checking duplicate after create for required document {self.id}: {str(e)}")
            import traceback
            _logger.error(f"Full traceback: {traceback.format_exc()}")

    @api.constrains('project_id', 'task_id', 'product_tmpl_id', 'document_type_id')
    def check_duplicate_document(self):
        """Check for duplicate required documents - SIMPLIFIED VERSION"""
        for record in self:
            if not record.document_type_id:
                continue
                
            # Build domain based on context
            domain = [
                ('document_type_id', '=', record.document_type_id.id),
                ('id', '!=', record.id)
            ]
            
            # Add context-specific filter
            if record.product_tmpl_id:
                domain.append(('product_tmpl_id', '=', record.product_tmpl_id.id))
                context_name = record.product_tmpl_id.name
            elif record.project_id:
                domain.append(('project_id', '=', record.project_id.id))
                context_name = record.project_id.name
            elif record.task_id:
                domain.append(('task_id', '=', record.task_id.id))
                context_name = record.task_id.name
            else:
                continue  # Skip if no context
            
            # Check for duplicates
            duplicates = self.search(domain)
            if duplicates:
                raise ValidationError(_(
                    "⚠️ Duplicate required document detected: '%s' already exists in '%s'"
                ) % (record.document_type_id.name, context_name))

    def write(self, vals):
        res = super(ProjectDocumentRequiredLine, self).write(vals)
        if vals.get('expiry_date'):
            self.write({'expiration_reminder_sent': False})
        if vals.get('attachment_ids'):
            self.write({'document_create_date': fields.Datetime.today()})
        return res

    def action_upload_document(self):
        """Action to upload document for this line"""
        self.ensure_one()
        return {
            'name': _('Upload Document'),
            'type': 'ir.actions.act_window',
            'res_model': 'document.upload.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_name': self.document_type_id.name,
                'default_document_type': 'required',
                'default_project_id': self.project_id.id if self.project_id else False,
                'default_task_id': self.task_id.id if self.task_id else False,
                'default_document_line_id': self.id,
            }
        }


# Temporarily disable NEW PROJECT-LEVEL DOCUMENT MODELS to isolate transaction issues
# --- NEW PROJECT-LEVEL DOCUMENT MODELS ---

if False:  # Disable these models temporarily
    class ProjectLevelRequiredDocument(models.Model):
        _name = 'project.level.required.document'
        _description = 'Project Level Required Document'
        _order = 'sequence, id'

        project_id = fields.Many2one('project.project', string='Project', required=True, ondelete='cascade')
        document_type_id = fields.Many2one('project.document.type', string='Document Type', required=True)
        document_id = fields.Many2one('documents.document', string='Document', required=True)
        sequence = fields.Integer(string='Sequence', default=10)
        is_required = fields.Boolean(string='Required', default=True)
        is_verified = fields.Boolean(string='Verified', default=False)
        verification_date = fields.Date(string='Verification Date')
        verified_by = fields.Many2one('res.users', string='Verified By')
        expiry_date = fields.Date('Expiry Date')
        reminder_days = fields.Integer('Reminder Days', default=30)
        is_expired = fields.Boolean('Is Expired', default=False)
        number = fields.Char(
            string="Number",
            required=True,
            copy=False,
            readonly=True,
            index=True,
            default=lambda self: _("New"),
        )
        issue_date = fields.Date(
            default=fields.Date.today,
            help="Date when the document was issued",
        )
        attachment_ids = fields.Many2many('ir.attachment', string='Attachments')
        expiration_reminder = fields.Boolean(default=False)
        expiration_reminder_sent = fields.Boolean(default=False)
        document_create_date = fields.Datetime(
            readonly=True,
            string="Document Create Date",
            default=fields.datetime.now(),
        )

        # @api.depends('expiry_date')
        # def _compute_expired(self):
        #     for record in self:
        #         record.is_expired = record.expiry_date and record.expiry_date < fields.Date.today()

        @api.model_create_multi
        def create(self, vals_list):
            for vals in vals_list:
                if 'number' not in vals:
                    vals['number'] = self.env['ir.sequence'].next_by_code('project.level.required.document') or _("New")
            return super(ProjectLevelRequiredDocument, self).create(vals_list)

        def action_upload_document(self):
            """Action to upload document for this line"""
            self.ensure_one()
            return {
                'name': _('Upload Document'),
                'type': 'ir.actions.act_window',
                'res_model': 'document.upload.wizard',
                'view_mode': 'form',
                'target': 'new',
                'context': {
                    'default_name': self.document_type_id.name,
                    'default_document_type': 'required',
                    'default_project_id': self.project_id.id,
                    'default_document_line_id': self.id,
                }
            }


    class ProjectLevelDeliverableDocument(models.Model):
        _name = 'project.level.deliverable.document'
        _description = 'Project Level Deliverable Document'
        _order = 'sequence, id'

        project_id = fields.Many2one('project.project', string='Project', required=True, ondelete='cascade')
        document_type_id = fields.Many2one('project.document.type', string='Document Type', required=True)
        document_id = fields.Many2one('documents.document', string='Document', required=True)
        sequence = fields.Integer(string='Sequence', default=10)
        is_required = fields.Boolean(string='Required', default=True)
        is_verified = fields.Boolean(string='Verified', default=False)
        verification_date = fields.Date(string='Verification Date')
        verified_by = fields.Many2one('res.users', string='Verified By')
        expiry_date = fields.Date('Expiry Date')
        reminder_days = fields.Integer('Reminder Days', default=30)
        is_expired = fields.Boolean('Is Expired', default=False)
        number = fields.Char(
            string="Number",
            required=True,
            copy=False,
            readonly=True,
            index=True,
            default=lambda self: _("New"),
        )
        issue_date = fields.Date(
            default=fields.Date.today,
            help="Date when the document was issued",
        )
        attachment_ids = fields.Many2many('ir.attachment', string='Attachments')
        expiration_reminder = fields.Boolean(default=False)
        expiration_reminder_sent = fields.Boolean(default=False)
        document_create_date = fields.Datetime(
            readonly=True,
            string="Document Create Date",
            default=fields.datetime.now(),
        )

        # @api.depends('expiry_date')
        # def _compute_expired(self):
        #     for record in self:
        #         record.is_expired = record.expiry_date and record.expiry_date < fields.Date.today()

        @api.model_create_multi
        def create(self, vals_list):
            for vals in vals_list:
                if 'number' not in vals:
                    vals['number'] = self.env['ir.sequence'].next_by_code('project.level.deliverable.document') or _("New")
            return super(ProjectLevelDeliverableDocument, self).create(vals_list)

        def action_upload_document(self):
            """Action to upload document for this line"""
            self.ensure_one()
            return {
                'name': _('Upload Document'),
                'type': 'ir.actions.act_window',
                'res_model': 'document.upload.wizard',
                'view_mode': 'form',
                'target': 'new',
                'context': {
                    'default_name': self.document_type_id.name,
                    'default_document_type': 'deliverable',
                    'default_project_id': self.project_id.id,
                    'default_document_line_id': self.id,
                }
            }

# End of disabled models block


class ProjectProject(models.Model):
    _inherit = 'project.project'

    # --- Existing fields (for backward compatibility) ---
    document_type_ids = fields.One2many(
        'project.document.type.line', 'project_id', string='Deliverable Document Types')
    document_required_type_ids = fields.One2many(
        'project.document.required.line', 'project_id', string='Required Document Types')
    # sale_order_id field is inherited from sale_project, do not redefine

    # Temporarily disable project-level document fields due to disabled models
    # # --- NEW PROJECT-LEVEL DOCUMENT FIELDS ---
    # project_required_document_ids = fields.One2many(
    #     'project.level.required.document', 'project_id', string='Project Required Documents')
    # project_deliverable_document_ids = fields.One2many(
    #     'project.level.deliverable.document', 'project_id', string='Project Deliverable Documents')

    # --- Workflow checkboxes for Required Documents ---
    required_document_complete = fields.Boolean(string="Required Document Complete", default=False)
    required_document_confirm = fields.Boolean(string="Required Document Confirm", default=False)
    required_document_update = fields.Boolean(string="Required Document Update", default=False)

    # --- Workflow checkboxes for Deliverable Documents ---
    deliverable_document_complete = fields.Boolean(string="Deliverable Document Complete", default=False)
    deliverable_document_confirm = fields.Boolean(string="Deliverable Document Confirm", default=False)
    deliverable_document_update = fields.Boolean(string="Deliverable Document Update", default=False)

    # --- Workflow checkboxes for Compliance ---
    is_complete_return_compliance = fields.Boolean(string="Compliance Complete", default=False)
    is_confirm_compliance = fields.Boolean(string="Compliance Confirm", default=False)
    is_update_compliance = fields.Boolean(string="Update Compliance", default=False)

    # --- Project-specific fields ---
    return_reason = fields.Text(string="Return Reason")
    return_date = fields.Date(string="Return Date")
    update_reason = fields.Text(string="Update Reason")
    update_date = fields.Date(string="Update Date")

    # --- Partner Related Fields (Compliance) ---
    project_field_ids = fields.One2many(
        "project.res.partner.fields",
        "project_id",
        string="Project Partner Fields",
        copy=False,
    )
    
    # --- Partner Fields Workflow checkboxes ---
    is_complete_partner_fields = fields.Boolean(string="Complete Partner Fields", default=False)
    is_confirm_partner_fields = fields.Boolean(string="Partner Fields Confirm", default=False)
    is_complete_return_partner_fields = fields.Boolean(string="Partner Fields Complete Return", default=False)
    is_second_complete_partner_fields_check = fields.Integer(string="Second Complete Partner Fields Check", default=0)
    is_update_partner_fields = fields.Boolean(string="Update Partner Fields", default=False)
    
    # --- Computed field for partner fields update check ---
    is_update_partner_fields_check = fields.Boolean(string="Update Partner Fields Check", compute="_compute_is_update_partner_fields_check")
    
    # --- Reached Checkpoints ---
    reached_checkpoint_ids = fields.Many2many(
        'reached.checkpoint', 
        string='Reached Checkpoints',
        help='Track checkpoints that have been reached in this project'
    )

    # --- Computed Summary Fields ---
    checkpoint_summary = fields.Text(
        string="Checkpoint Summary", 
        compute='_compute_checkpoint_summary',
        help="Summary of all checkpoint statuses"
    )
    
    @api.depends('is_update_partner_fields')
    def _compute_is_update_partner_fields_check(self):
        for record in self:
            record.is_update_partner_fields_check = record.is_update_partner_fields

    @api.depends('required_document_complete', 'required_document_confirm', 'required_document_update',
                 'deliverable_document_complete', 'deliverable_document_confirm', 'deliverable_document_update',
                 'is_complete_return_compliance', 'is_confirm_compliance', 'is_update_compliance',
                 'is_complete_partner_fields', 'is_confirm_partner_fields', 'is_update_partner_fields',
                 'is_handover_complete')
    def _compute_checkpoint_summary(self):
        """Compute a summary of all checkpoint statuses."""
        for project in self:
            summary = []
            
            # Required Documents
            if project.required_document_complete:
                summary.append(_("Required Documents Complete"))
            if project.required_document_confirm:
                summary.append(_("Required Documents Confirmed"))
            if project.required_document_update:
                summary.append(_("Required Documents Updated"))
            
            # Deliverable Documents  
            if project.deliverable_document_complete:
                summary.append(_("Deliverable Documents Complete"))
            if project.deliverable_document_confirm:
                summary.append(_("Deliverable Documents Confirmed"))
            if project.deliverable_document_update:
                summary.append(_("Deliverable Documents Updated"))
            
            # Compliance
            if project.is_complete_return_compliance:
                summary.append(_("Compliance Complete"))
            if project.is_confirm_compliance:
                summary.append(_("Compliance Confirmed"))
            if project.is_update_compliance:
                summary.append(_("Compliance Updated"))
            
            # Partner Fields
            if project.is_complete_partner_fields:
                summary.append(_("Partner Fields Complete"))
            if project.is_confirm_partner_fields:
                summary.append(_("Partner Fields Confirmed"))
            if project.is_update_partner_fields:
                summary.append(_("Partner Fields Updated"))
            
            # Handover
            if project.is_handover_complete:
                summary.append(_("Handover Complete"))
            
            project.checkpoint_summary = "\n".join(summary) if summary else _("No checkpoints completed")

    # --- Project Notes (Compliance & Handover) ---
    compliance_notes = fields.Html(
        string="Compliance Notes",
        help="Notes related to compliance requirements and status for this project"
    )
    
    handover_notes = fields.Html(
        string="Handover Notes", 
        help="Notes for project handover including deliverables, access, and instructions"
    )
    
    internal_notes = fields.Html(
        string="Internal Notes",
        help="Internal project notes for team reference"
    )
    
    client_notes = fields.Html(
        string="Client Notes",
        help="Notes visible to client or for client communication"
    )
    
    # --- Handover Status Fields ---
    is_handover_complete = fields.Boolean(
        string="Handover Complete",
        default=False,
        help="Mark when project handover is complete"
    )
    
    handover_date = fields.Date(
        string="Handover Date",
        help="Date when project was handed over to client"
    )
    
    handover_by = fields.Many2one(
        'res.users',
        string="Handed Over By",
        help="User who completed the handover"
    )

    @api.model_create_multi
    def create(self, vals_list):
        projects = super().create(vals_list)
        # Temporarily disable document copying again to isolate transaction issues
        # for project in projects:
        #     # Try to get product templates from sale order lines if available
        #     sale_line_id = project.sale_line_id.id if hasattr(project, 'sale_line_id') and project.sale_line_id else None
        #     product_templates = []
        #     if sale_line_id:
        #         sale_line = self.env['sale.order.line'].browse(sale_line_id)
        #         if sale_line and sale_line.product_id:
        #             product_templates.append(sale_line.product_id.product_tmpl_id)
        #     # Optionally, add logic to get product templates from context if needed
        #     if product_templates:
        #         try:
        #             copy_documents_from_product_to_project(self.env, project, product_templates)
        #         except Exception as e:
        #             # Log the error but don't fail project creation
        #             _logger.warning(f"Failed to copy documents from product template: {e}")
        return projects

    # Re-enable project-level document management methods
    # --- Project-level document management methods ---
    def action_complete_required_documents(self):
        """Complete required documents for project"""
        self.ensure_one()
        self.required_document_complete = True
        self.message_post(body="✅ Required documents marked as complete")
        return True

    def action_confirm_required_documents(self):
        """Confirm required documents for project"""
        self.ensure_one()
        self.required_document_confirm = True
        self.message_post(body="✅ Required documents completion confirmed")
        return True

    def action_update_required_documents(self):
        """Update required documents for project"""
        self.ensure_one()
        self.required_document_update = True
        self.message_post(body="🔄 Required documents marked for update")
        return True

    def action_reset_required_document_complete(self):
        """Reset required document complete status"""
        self.ensure_one()
        self.required_document_complete = False
        return True

    def action_reset_required_document_confirm(self):
        """Reset required document confirm status"""
        self.ensure_one()
        self.required_document_confirm = False
        return True

    def action_reset_required_document_update(self):
        """Reset required document update status"""
        self.ensure_one()
        self.required_document_update = False
        return True

    def action_complete_deliverable_documents(self):
        """Complete deliverable documents for project"""
        self.ensure_one()
        self.deliverable_document_complete = True
        self.message_post(body="✅ Deliverable documents marked as complete")
        return True

    def action_confirm_deliverable_documents(self):
        """Confirm deliverable documents for project"""
        self.ensure_one()
        self.deliverable_document_confirm = True
        self.message_post(body="✅ Deliverable documents completion confirmed")
        return True

    def action_update_deliverable_documents(self):
        """Update deliverable documents for project"""
        self.ensure_one()
        self.deliverable_document_update = True
        self.message_post(body="🔄 Deliverable documents marked for update")
        return True

    def action_reset_deliverable_document_complete(self):
        """Reset deliverable document complete status"""
        self.ensure_one()
        self.deliverable_document_complete = False
        return True

    def action_reset_deliverable_document_confirm(self):
        """Reset deliverable document confirm status"""
        self.ensure_one()
        self.deliverable_document_confirm = False
        return True

    def action_reset_deliverable_document_update(self):
        """Reset deliverable document update status"""
        self.ensure_one()
        self.deliverable_document_update = False
        return True

    # --- Compliance Action Methods ---
    def action_complete_compliance(self):
        """Mark compliance as complete"""
        self.ensure_one()
        self.is_complete_return_compliance = True
        self.message_post(body="✅ Compliance marked as complete")
        return True

    def action_confirm_compliance(self):
        """Confirm compliance completion"""
        self.ensure_one()
        self.is_confirm_compliance = True
        self.message_post(body="✅ Compliance completion confirmed")
        return True

    def action_update_compliance(self):
        """Mark compliance for update"""
        self.ensure_one()
        self.is_update_compliance = True
        self.message_post(body="🔄 Compliance marked for update")
        return True

    def action_reset_compliance_complete(self):
        """Reset compliance complete status"""
        self.ensure_one()
        self.is_complete_return_compliance = False
        return True

    def action_reset_compliance_confirm(self):
        """Reset compliance confirm status"""
        self.ensure_one()
        self.is_confirm_compliance = False
        return True

    def action_reset_compliance_update(self):
        """Reset compliance update status"""
        self.ensure_one()
        self.is_update_compliance = False
        return True


class ProjectTask(models.Model):
    _inherit = 'project.task'

    document_required_type_ids = fields.One2many(
        'project.document.required.line', 'task_id', string='Required Document Types')
    document_type_ids = fields.One2many(
        'project.document.type.line', 'task_id', string='Deliverable Document Types')

    # Task-level workflow fields (matching original pattern)
    required_document_complete = fields.Boolean(string="Required Document Complete", default=False)
    required_document_confirm = fields.Boolean(string="Required Document Confirm", default=False)
    required_document_update = fields.Boolean(string="Required Document Update", default=False)
    
    deliverable_document_complete = fields.Boolean(string="Deliverable Document Complete", default=False)
    deliverable_document_confirm = fields.Boolean(string="Deliverable Document Confirm", default=False)
    deliverable_document_update = fields.Boolean(string="Deliverable Document Update", default=False)

    # Task-level workflow action methods (matching original pattern)
    def action_complete_required_documents(self):
        """Complete required documents for task"""
        self.ensure_one()
        self.required_document_complete = True
        self.message_post(body="✅ Required documents marked as complete")
        return True

    def action_confirm_required_documents(self):
        """Confirm required documents for task"""
        self.ensure_one()
        self.required_document_confirm = True
        self.message_post(body="✅ Required documents completion confirmed")
        return True

    def action_update_required_documents(self):
        """Update required documents for task"""
        self.ensure_one()
        self.required_document_update = True
        self.message_post(body="🔄 Required documents marked for update")
        return True

    def action_reset_required_document_complete(self):
        """Reset required document complete status"""
        self.ensure_one()
        self.required_document_complete = False
        return True

    def action_reset_required_document_confirm(self):
        """Reset required document confirm status"""
        self.ensure_one()
        self.required_document_confirm = False
        return True

    def action_reset_required_document_update(self):
        """Reset required document update status"""
        self.ensure_one()
        self.required_document_update = False
        return True

    def action_complete_deliverable_documents(self):
        """Complete deliverable documents for task"""
        self.ensure_one()
        self.deliverable_document_complete = True
        self.message_post(body="✅ Deliverable documents marked as complete")
        return True

    def action_confirm_deliverable_documents(self):
        """Confirm deliverable documents for task"""
        self.ensure_one()
        self.deliverable_document_confirm = True
        self.message_post(body="✅ Deliverable documents completion confirmed")
        return True

    def action_update_deliverable_documents(self):
        """Update deliverable documents for task"""
        self.ensure_one()
        self.deliverable_document_update = True
        self.message_post(body="🔄 Deliverable documents marked for update")
        return True

    def action_reset_deliverable_document_complete(self):
        """Reset deliverable document complete status"""
        self.ensure_one()
        self.deliverable_document_complete = False
        return True

    def action_reset_deliverable_document_confirm(self):
        """Reset deliverable document confirm status"""
        self.ensure_one()
        self.deliverable_document_confirm = False
        return True

    def action_reset_deliverable_document_update(self):
        """Reset deliverable document update status"""
        self.ensure_one()
        self.deliverable_document_update = False
        return True



    @api.model_create_multi
    def create(self, vals_list):
        tasks = super().create(vals_list)
        for task in tasks:
            project = task.project_id
            if project:
                try:
                    copy_documents_from_project_to_task(task.env, task, project)
                except Exception as e:
                    # Log the error but don't fail task creation
                    _logger.warning(f"Failed to copy documents from project to task: {e}")
        return tasks

    def action_copy_checkpoints_from_template(self):
        """Manual action to copy checkpoints from product task template"""
        for task in self:
            if task.project_id and task.project_id.sale_order_id:
                # Find matching product task template
                sale_order = task.project_id.sale_order_id
                for line in sale_order.order_line:
                    if line.product_id.service_tracking == 'new_workflow':
                        for template in line.product_id.product_tmpl_id.task_template_ids:
                            if template.name == task.name:
                                try:
                                    # Clear existing checkpoints first
                                    task.task_checkpoint_ids.unlink()
                                    # Copy from template
                                    copy_checkpoints_from_template_to_task(task.env, task, template)
                                    task.message_post(body=f"Checkpoints copied from template: {template.name}")
                                    return {
                                        'type': 'ir.actions.client',
                                        'tag': 'display_notification',
                                        'params': {
                                            'title': 'Success',
                                            'message': f'Checkpoints copied from template: {template.name}',
                                            'type': 'success',
                                            'sticky': False,
                                        }
                                    }
                                except Exception as e:
                                    return {
                                        'type': 'ir.actions.client',
                                        'tag': 'display_notification',
                                        'params': {
                                            'title': 'Error',
                                            'message': f'Failed to copy checkpoints: {str(e)}',
                                            'type': 'danger',
                                            'sticky': True,
                                        }
                                    }


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    # Temporarily disable computed fields to isolate transaction issues
    # project_ids = fields.Many2many('project.project', compute='_compute_project_ids', string='Projects', store=False)
    # project_count = fields.Integer(string='Number of Projects', compute='_compute_project_ids', store=False)

    # def _compute_project_ids(self):
    #     is_project_manager = self.env.user.has_group('project.group_project_manager')
    #     projects = self.env['project.project'].search([
    #         ('sale_order_id', 'in', self.ids)
    #     ])
    #     projects_per_so = defaultdict(lambda: self.env['project.project'])
    #     for project in projects:
    #         projects_per_so[project.sale_order_id.id] |= project

    #     for order in self:
    #         # Fetch projects from various sources
    #         projects = order.order_line.mapped('product_id.project_id')
    #         projects |= order.order_line.mapped('project_id')
    #         projects |= projects_per_so[order.id or order._origin.id]
    #         # Restrict projects if user is not a project manager
    #         if not is_project_manager:
    #             projects = projects._filter_access_rules('read')
    #         order.project_ids = projects
    #         order.project_count = len(projects)

    def action_confirm(self):
        _logger.info(f"🚀 ACTION_CONFIRM called for sale order: {self.name} (ID: {self.id})")
        res = super().action_confirm()
        # Re-enable project creation but keep task creation disabled
        _logger.info(f"🚀 About to call _create_tasks_from_templates for order: {self.name}")
        self._create_tasks_from_templates()
        return res

    def _create_tasks_from_templates(self):
        for order in self:
            try:
                _logger.info(f"🔍 Processing sale order: {order.name} (ID: {order.id})")
                
                all_workflow_products = order.order_line.mapped('product_id').filtered(
                    lambda p: p.service_tracking == 'new_workflow'
                )
                _logger.info(f"🔍 Found {len(all_workflow_products)} products with service_tracking='new_workflow':")
                for product in all_workflow_products:
                    _logger.info(f"  - {product.name} (ID: {product.id}, Service Tracking: {product.service_tracking})")
                
                if not all_workflow_products:
                    _logger.info(f"❌ No workflow products found for order {order.name}, skipping")
                    continue
                
                # Find or create project for this order
                # Fix: Use sale_line_id.order_id instead of sale_order_id
                projects = self.env['project.project'].search([('sale_line_id.order_id', '=', order.id)])
                _logger.info(f"🔍 Found {len(projects)} existing projects for order {order.name}")
                
                if not projects:
                    _logger.info(f"🔨 Creating new project for order {order.name}")
                    # Pass context for document propagation
                    ctx = self.env.context.copy()
                    if order.order_line:
                        ctx['default_sale_order_line_id'] = order.order_line[0].id
                    project = self.env["project.project"].with_context(ctx).create({
                        "name": f"{order.name} - {order.partner_id.name}",
                        "sale_line_id": order.order_line[0].id if order.order_line else False,
                        "user_id": order.user_id.id,
                        "partner_id": order.partner_id.id,
                    })
                    projects = project
                    _logger.info(f"✅ Created project: {project.name} (ID: {project.id})")
                    
                    # Copy documents from product templates to project using Document Service
                    try:
                        _logger.info(f"🔧 Using Document Service to copy documents")
                        document_service = self.env['document.service']
                        documents_created = document_service.create_smart_documents(project, order)
                        _logger.info(f"📋 Document service results: {documents_created}")
                        
                        # Post results to the project
                        project.message_post(
                            body=f"Smart Document Service Results:<br/>"
                                 f"• Created {documents_created.get('deliverable', 0)} deliverable document lines<br/>"
                                 f"• Created {documents_created.get('required', 0)} required document lines<br/>"
                                 f"• Prevented {documents_created.get('duplicates_prevented', 0)} duplicates"
                        )
                    except Exception as e:
                        _logger.error(f"❌ Failed to use document service: {e}")
                        import traceback
                        _logger.error(f"Full traceback: {traceback.format_exc()}")
                else:
                    _logger.info(f"📁 Using existing projects: {[p.name for p in projects]}")
                    
                # Re-enable task creation
                # Create tasks for each project using the service
                _logger.info(f"🔨 Creating tasks for {len(projects)} projects")
                for project in projects:
                    _logger.info(f"  Processing project: {project.name}")
                    for product in all_workflow_products:
                        _logger.info(f"    Processing product: {product.name}")
                        if product.product_tmpl_id.task_template_ids:
                            _logger.info(f"      Found {len(product.product_tmpl_id.task_template_ids)} task templates")
                            for template in product.product_tmpl_id.task_template_ids:
                                try:
                                    task = self.env['project.task'].create({
                                        'name': template.name,
                                        'project_id': project.id,
                                        'description': template.description,
                                        'user_ids': [(6, 0, template.user_ids.ids)],
                                        'stage_id': template.stage_id.id if template.stage_id else False,
                                        'allocated_hours': template.planned_hours,
                                        'priority': template.priority,
                                    })
                                    _logger.info(f"      ✅ Created task: {task.name} (ID: {task.id})")
                                    
                                    # Copy checkpoints from template to task
                                    try:
                                        copy_checkpoints_from_template_to_task(task.env, task, template)
                                        _logger.info(f"      📋 Copied checkpoints from template to task: {task.name}")
                                    except Exception as checkpoint_error:
                                        _logger.warning(f"      ⚠️ Failed to copy checkpoints for task {task.name}: {checkpoint_error}")
                                    
                                except Exception as e:
                                    _logger.warning(f"      ❌ Failed to create task from template {template.name}: {e}")
                                    continue
                        else:
                            _logger.info(f"      No task templates found for product {product.name}")
            except Exception as e:
                _logger.error(f"❌ Failed to create projects from templates for order {order.name}: {e}")
                import traceback
                _logger.error(f"Full traceback: {traceback.format_exc()}")
                continue 