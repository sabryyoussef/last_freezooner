from odoo import api, models
import logging
from odoo import fields

_logger = logging.getLogger(__name__)


class ProjectDocumentService(models.AbstractModel):
    """Enhanced service class to handle document creation for projects with smart duplicate detection"""
    _name = 'project.document.service'
    _description = 'Project Document Service'

    @api.model
    def create_smart_documents(self, project, sale_order):
        """
        Create documents with smart duplicate detection
        Will link existing documents instead of creating duplicates
        Args:
            project: project.project record
            sale_order: sale.order record
        Returns:
            dict with creation statistics
        """
        _logger.info(f"=== SMART DOCUMENT SERVICE: Creating documents for project {project.name} ===")
        
        # Get all order lines with new_workflow products
        workflow_lines = sale_order.order_line.filtered(
            lambda line: line.product_id.service_tracking == "new_workflow"
        )
        
        _logger.info(f"Found {len(workflow_lines)} order lines with new_workflow products")
        
        documents_created = {
            'deliverable': 0,
            'required': 0,
            'existing_linked': 0,
            'duplicates_prevented': 0,
            'milestone_based': 0
        }

        # Deduplication sets for this project
        deliverable_keys = set()
        required_keys = set()
        deliverable_types = []
        required_types = []

        for line in workflow_lines:
            product = line.product_id
            product_template = product.product_tmpl_id

            # Collect unique deliverable document types (x_ fields)
            _logger.info(f"Product {product_template.name} has {len(getattr(product_template, 'x_deliverable_document_ids', []))} x_deliverable_document_ids")
            for doc in getattr(product_template, 'x_deliverable_document_ids', []):
                doc_type_field = getattr(doc, 'x_document_type_id', None) or getattr(doc, 'document_type_id', None)
                _logger.info(f"Checking x_deliverable_document: {doc} with doc_type_field: {doc_type_field}")
                if doc_type_field:
                    key = (project.id, doc_type_field.id, sale_order.partner_id.id)
                    if key not in deliverable_keys:
                        deliverable_keys.add(key)
                        deliverable_types.append(doc)

            # Collect unique required document types (x_ fields)
            _logger.info(f"Product {product_template.name} has {len(getattr(product_template, 'x_required_document_ids', []))} x_required_document_ids")
            for doc in getattr(product_template, 'x_required_document_ids', []):
                doc_type_field = getattr(doc, 'x_document_type_id', None) or getattr(doc, 'document_type_id', None)
                _logger.info(f"Checking x_required_document: {doc} with doc_type_field: {doc_type_field}")
                if doc_type_field:
                    key = (project.id, doc_type_field.id, sale_order.partner_id.id)
                    if key not in required_keys:
                        required_keys.add(key)
                        required_types.append(doc)

        # Process deliverable documents with smart duplicate detection
        for doc_type in deliverable_types:
            result = self._create_or_link_document(
                project, doc_type, sale_order.partner_id, 'deliverable'
            )
            documents_created[result['action']] += 1

        # Process required documents with smart duplicate detection  
        for doc_type in required_types:
            result = self._create_or_link_document(
                project, doc_type, sale_order.partner_id, 'required'
            )
            documents_created[result['action']] += 1

        _logger.info(f"Smart document creation completed: {documents_created}")
        return documents_created

    def _create_or_link_document(self, project, doc_type, partner, doc_category):
        """
        Create new document or link existing one based on duplicate detection
        Args:
            project: project.project record
            doc_type: document type configuration
            partner: res.partner record
            doc_category: 'deliverable' or 'required'
        Returns:
            dict with action taken and document info
        """
        # Support both legacy and x_ models
        document_type = getattr(doc_type, 'x_document_type_id', None) or getattr(doc_type, 'document_type_id', None)
        
        # Enhanced duplicate detection - check existing document lines
        existing_doc_lines = self._find_existing_document_lines(project, document_type, doc_category)
        
        _logger.info(f"Checking documents for partner {partner.name}, type {getattr(document_type, 'name', document_type)}")
        _logger.info(f"Found {len(existing_doc_lines)} potential matches")
        
        if existing_doc_lines:
            # Link to existing document line
            existing_line = existing_doc_lines[0]  # Take the first match
            doc_type_field = getattr(existing_line, 'x_document_type_id', None) or getattr(existing_line, 'document_type_id', None)
            _logger.info(f"🔗 Linked existing document line: {getattr(doc_type_field, 'name', doc_type_field)}")
            
            # Post message to project
            link_message = f"""
                <b>Document Linked:</b><br/>
                • Name: {getattr(doc_type_field, 'name', doc_type_field)}<br/>
                • Category: {doc_category}<br/>
                • Partner: {partner.name}<br/>
            """
            project.message_post(body=link_message)
            
            return {
                'action': 'existing_linked',
                'document': existing_line,
                'message': f"Linked existing document to project"
            }
        else:
            # Create new document line
            new_doc_line = self._create_document_line(project, doc_type, partner, doc_category)
            doc_type_field = getattr(new_doc_line, 'x_document_type_id', None) or getattr(new_doc_line, 'document_type_id', None)
            _logger.info(f"📝 Created new document line: {getattr(doc_type_field, 'name', doc_type_field)}")
            
            return {
                'action': doc_category,
                'document': new_doc_line,
                'message': f"Created new {doc_category} document"
            }

    def _find_existing_document_lines(self, project, document_type, doc_category):
        """
        Find existing document lines with enhanced matching
        Args:
            project: project.project record
            document_type: project.document.type record
            doc_category: 'deliverable' or 'required'
        Returns:
            recordset of existing document lines
        """
        if doc_category == 'deliverable':
            existing_lines = self.env['project.deliverable.document'].search([
                ('x_project_id', '=', project.id),
                ('x_document_type_id', '=', document_type.id)
            ])
        else:  # required
            existing_lines = self.env['project.required.document'].search([
                ('x_project_id', '=', project.id),
                ('x_document_type_id', '=', document_type.id)
            ])
        
        return existing_lines

    def _create_document_line(self, project, doc_type, partner, doc_category):
        """
        Create new document line
        Args:
            project: project.project record
            doc_type: document type configuration
            partner: res.partner record
            doc_category: 'deliverable' or 'required'
        Returns:
            document line record
        """
        document_type = getattr(doc_type, 'x_document_type_id', None) or getattr(doc_type, 'document_type_id', None)
        is_required = getattr(doc_type, 'x_is_required', None)
        if is_required is None:
            is_required = getattr(doc_type, 'is_required', False)
        expiry_date = getattr(doc_type, 'x_expiry_date', None)
        if expiry_date is None:
            expiry_date = getattr(doc_type, 'expiry_date', False)
        reminder_days = getattr(doc_type, 'x_reminder_days', None)
        if reminder_days is None:
            reminder_days = getattr(doc_type, 'reminder_days', 30)
        name = getattr(doc_type, 'name', None) or (document_type and document_type.name) or 'Document'
        # Create x_ document line instead of legacy line
        if doc_category == 'deliverable':
            document_line = self.env['project.deliverable.document'].sudo().create({
                'x_project_id': project.id,
                'x_document_type_id': document_type.id,
                'x_is_required': is_required,
                'x_expiry_date': expiry_date,
                'x_reminder_days': reminder_days,
                'name': name,
            })
        else:
            _logger.info(f"[REQUIRED DEBUG] Creating project.required.document with: x_project_id={project.id}, x_document_type_id={getattr(document_type, 'id', None)}, x_is_required={is_required}, x_expiry_date={expiry_date}, x_reminder_days={reminder_days}, name={name}")
            document_line = self.env['project.required.document'].sudo().create({
                'x_project_id': project.id,
                'x_document_type_id': document_type.id,
                'x_is_required': is_required,
                'x_expiry_date': expiry_date,
                'x_reminder_days': reminder_days,
                'name': name,
            })
        # Log creation
        doc_type_field = getattr(document_line, 'x_document_type_id', None) or getattr(document_line, 'document_type_id', None)
        creation_message = f"""
            <b>New x_Document Created:</b><br/>
            • Name: {document_line.name}<br/>
            • Category: {doc_category}<br/>
            • Partner: {partner.name}<br/>
            • Required: {getattr(document_line, 'x_is_required', getattr(document_line, 'is_required', ''))}<br/>
        """
        _logger.info(f"📝 Created new document line: {getattr(doc_type_field, 'name', doc_type_field)}")
        project.message_post(body=creation_message)
        return document_line

    def _is_valid_document_type(self, doc_type):
        """
        Check if document type is valid for creation
        Args:
            doc_type: document type configuration
        Returns:
            bool: True if valid, False otherwise
        """
        document_type = getattr(doc_type, 'x_document_type_id', None) or getattr(doc_type, 'document_type_id', None)
        if not document_type:
            return False
        if not getattr(document_type, 'name', None):
            return False
        return True

    @api.model
    def copy_documents_from_project_to_task(self, task, project):
        """
        Copy x_ required and deliverable documents from project to task.
        Args:
            task: project.task record
            project: project.project record
        Returns:
            dict with copy statistics
        """
        _logger.info(f"=== COPYING x_ DOCUMENTS FROM PROJECT TO TASK ===")
        copy_stats = {
            'deliverable_copied': 0,
            'required_copied': 0,
            'duplicates_prevented': 0
        }
        # Copy x_ deliverable documents from product template to project (with attachments)
        for doc in getattr(product_template, 'x_deliverable_document_ids', []):
            doc_type_field = getattr(doc, 'x_document_type_id', None) or getattr(doc, 'document_type_id', None)
            if doc_type_field:
                key = (project.id, doc_type_field.id, sale_order.partner_id.id)
                if key not in deliverable_keys:
                    deliverable_keys.add(key)
                    new_doc = self.env['project.deliverable.document'].sudo().create({
                        'x_project_id': project.id,
                        'x_document_type_id': doc.x_document_type_id.id,
                        'x_is_required': doc.x_is_required,
                        'x_expiry_date': doc.x_expiry_date,
                        'x_reminder_days': doc.x_reminder_days,
                        'name': doc.name,
                        'x_attachment_ids': [(6, 0, doc.x_attachment_ids.ids)],
                    })
                    deliverable_types.append(new_doc)

        # Copy x_ required documents from product template to project (with attachments)
        for doc in getattr(product_template, 'x_required_document_ids', []):
            doc_type_field = getattr(doc, 'x_document_type_id', None) or getattr(doc, 'document_type_id', None)
            if doc_type_field:
                key = (project.id, doc_type_field.id, sale_order.partner_id.id)
                if key not in required_keys:
                    required_keys.add(key)
                    new_doc = self.env['project.required.document'].sudo().create({
                        'x_project_id': project.id,
                        'x_document_type_id': doc.x_document_type_id.id,
                        'x_is_required': doc.x_is_required,
                        'x_expiry_date': doc.x_expiry_date,
                        'x_reminder_days': doc.x_reminder_days,
                        'name': doc.name,
                        'x_attachment_ids': [(6, 0, doc.x_attachment_ids.ids)],
                    })
                    required_types.append(new_doc)
        _logger.info(f"x_ Document copy completed: {copy_stats}")
        return copy_stats

    @api.model
    def debug_smart_documents(self, project_id, sale_order_id):
        """
        Debug method to test smart document creation
        Args:
            project_id: project ID
            sale_order_id: sale order ID
        Returns:
            dict with debug information
        """
        project = self.env['project.project'].browse(project_id)
        sale_order = self.env['sale.order'].browse(sale_order_id)
        
        debug_info = {
            'project_name': project.name,
            'sale_order_name': sale_order.name,
            'workflow_products': [],
            'document_types': [],
            'existing_documents': []
        }
        
        # Get workflow products
        workflow_lines = sale_order.order_line.filtered(
            lambda line: line.product_id.service_tracking == "new_workflow"
        )
        
        for line in workflow_lines:
            product = line.product_id
            debug_info['workflow_products'].append({
                'name': product.name,
                'template_name': product.product_tmpl_id.name,
                # Commented out legacy deliverable document statistics/debug
                # 'deliverable_docs': len(product.product_tmpl_id.document_type_ids),
                'required_docs': len(product.product_tmpl_id.document_required_type_ids)
            })
        
        # Get existing documents
        debug_info['existing_documents'] = {
            'deliverable': len(project.x_deliverable_document_ids),
            'required': len(project.x_required_document_ids)
        }
        
        return debug_info 