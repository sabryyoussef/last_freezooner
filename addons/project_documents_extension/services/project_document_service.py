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

            # Collect unique deliverable document types
            for doc_type in product_template.document_type_ids:
                if self._is_valid_document_type(doc_type):
                    key = (project.id, doc_type.document_type_id.id, sale_order.partner_id.id)
                    if key not in deliverable_keys:
                        deliverable_keys.add(key)
                        deliverable_types.append(doc_type)

            # Collect unique required document types
            for doc_type in product_template.document_required_type_ids:
                if self._is_valid_document_type(doc_type):
                    key = (project.id, doc_type.document_type_id.id, sale_order.partner_id.id)
                    if key not in required_keys:
                        required_keys.add(key)
                        required_types.append(doc_type)

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
        document_type = doc_type.document_type_id
        
        # Enhanced duplicate detection - check existing document lines
        existing_doc_lines = self._find_existing_document_lines(project, document_type, doc_category)
        
        _logger.info(f"Checking documents for partner {partner.name}, type {document_type.name}")
        _logger.info(f"Found {len(existing_doc_lines)} potential matches")
        
        if existing_doc_lines:
            # Link to existing document line
            existing_line = existing_doc_lines[0]  # Take the first match
            _logger.info(f"🔗 Linked existing document line: {existing_line.document_type_id.name}")
            
            # Post message to project
            link_message = f"""
                <b>Document Linked:</b><br/>
                • Name: {existing_line.document_type_id.name}<br/>
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
            _logger.info(f"📝 Created new document line: {new_doc_line.document_type_id.name}")
            
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
            existing_lines = self.env['project.document.type.line'].search([
                ('project_id', '=', project.id),
                ('document_type_id', '=', document_type.id)
            ])
        else:  # required
            existing_lines = self.env['project.document.required.line'].search([
                ('project_id', '=', project.id),
                ('document_type_id', '=', document_type.id)
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
        document_vals = {
            'project_id': project.id,
            'document_type_id': doc_type.document_type_id.id,
            'is_required': doc_type.is_required,
            'expiry_date': doc_type.expiry_date if hasattr(doc_type, 'expiry_date') else False,
            'reminder_days': doc_type.reminder_days if hasattr(doc_type, 'reminder_days') else 30,
        }
        
        if doc_category == 'deliverable':
            document_line = self.env['project.document.type.line'].sudo().create(document_vals)
        else:
            document_line = self.env['project.document.required.line'].sudo().create(document_vals)
        
        # Log creation
        creation_message = f"""
            <b>New Document Created:</b><br/>
            • Name: {document_line.document_type_id.name}<br/>
            • Category: {doc_category}<br/>
            • Partner: {partner.name}<br/>
            • Required: {document_line.is_required}<br/>
        """
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
        if not doc_type.document_type_id:
            return False
        
        if not doc_type.document_type_id.name:
            return False
            
        return True

    @api.model
    def copy_documents_from_project_to_task(self, task, project):
        """
        Copy documents from project to task with smart duplicate detection
        Args:
            task: project.task record
            project: project.project record
        Returns:
            dict with copy statistics
        """
        _logger.info(f"=== COPYING DOCUMENTS FROM PROJECT TO TASK ===")
        
        copy_stats = {
            'deliverable_copied': 0,
            'required_copied': 0,
            'duplicates_prevented': 0
        }
        
        # Copy deliverable documents
        for doc_line in project.document_type_ids:
            existing_task_doc = self.env['project.document.type.line'].search([
                ('task_id', '=', task.id),
                ('document_type_id', '=', doc_line.document_type_id.id)
            ])
            
            if not existing_task_doc:
                self.env['project.document.type.line'].sudo().create({
                    'task_id': task.id,
                    'document_type_id': doc_line.document_type_id.id,
                    'is_required': doc_line.is_required,
                    'expiry_date': doc_line.expiry_date,
                    'reminder_days': doc_line.reminder_days,
                })
                copy_stats['deliverable_copied'] += 1
            else:
                copy_stats['duplicates_prevented'] += 1
        
        # Copy required documents
        for doc_line in project.document_required_type_ids:
            existing_task_doc = self.env['project.document.required.line'].search([
                ('task_id', '=', task.id),
                ('document_type_id', '=', doc_line.document_type_id.id)
            ])
            
            if not existing_task_doc:
                self.env['project.document.required.line'].sudo().create({
                    'task_id': task.id,
                    'document_type_id': doc_line.document_type_id.id,
                    'is_required': doc_line.is_required,
                    'expiry_date': doc_line.expiry_date,
                    'reminder_days': doc_line.reminder_days,
                })
                copy_stats['required_copied'] += 1
            else:
                copy_stats['duplicates_prevented'] += 1
        
        _logger.info(f"Document copy completed: {copy_stats}")
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
                'deliverable_docs': len(product.product_tmpl_id.document_type_ids),
                'required_docs': len(product.product_tmpl_id.document_required_type_ids)
            })
        
        # Get existing documents
        debug_info['existing_documents'] = {
            'deliverable': len(project.document_type_ids),
            'required': len(project.document_required_type_ids)
        }
        
        return debug_info 