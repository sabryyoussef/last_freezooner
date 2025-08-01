from odoo import models, api
import logging
from odoo import fields

_logger = logging.getLogger(__name__)


class DocumentService(models.AbstractModel):
    """Service class to handle document creation for projects"""
    _name = 'document.service'
    _description = 'Document Service'

    @api.model
    def check_existing_documents(self, project, doc_type, product_tmpl):
        """
        Check for existing document lines with same project, type, and product template
        Args:
            project: project.project record
            doc_type: document type record 
            product_tmpl: product template record
        Returns:
            boolean indicating if documents exist
        """
        _logger.info(f"🔍 Checking for existing documents: Project={project.name}, Type={doc_type.name if doc_type else 'None'}, Template={product_tmpl.name}")
        
        # Check deliverable documents
        existing_deliverable = self.env['project.document.type.line'].search([
            ('project_id', '=', project.id),
            ('document_type_id', '=', doc_type.id),
            ('product_tmpl_id', '=', product_tmpl.id)
        ])
        
        # Check required documents  
        existing_required = self.env['project.document.required.line'].search([
            ('project_id', '=', project.id),
            ('document_type_id', '=', doc_type.id),
            ('product_tmpl_id', '=', product_tmpl.id)
        ])
        
        # Return True if any exist (don't try to union different models)
        has_existing = len(existing_deliverable) > 0 or len(existing_required) > 0
        
        if has_existing:
            _logger.info(f"✅ Found existing document line(s): deliverable={len(existing_deliverable)}, required={len(existing_required)}")
        else:
            _logger.info(f"❌ No existing document lines found")
            
        return has_existing

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
            'duplicates_prevented': 0
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
            if hasattr(product_template, 'document_type_ids'):
                for doc_type in product_template.document_type_ids:
                    if self._is_valid_document_type(doc_type):
                        key = (project.id, doc_type.document_type_id.id, product_template.id)
                        if key not in deliverable_keys:
                            deliverable_keys.add(key)
                            deliverable_types.append(doc_type)

            # Collect unique required document types
            if hasattr(product_template, 'document_required_type_ids'):
                for doc_type in product_template.document_required_type_ids:
                    if self._is_valid_document_type(doc_type):
                        key = (project.id, doc_type.document_type_id.id, product_template.id)
                        if key not in required_keys:
                            required_keys.add(key)
                            required_types.append(doc_type)

        _logger.info(f"Collected {len(deliverable_types)} unique deliverable and {len(required_types)} unique required document types")

        # Create deliverable documents
        deliverable_count = self._create_deliverable_documents(project, deliverable_types)
        documents_created['deliverable'] = deliverable_count

        # Create required documents
        required_count = self._create_required_documents(project, required_types)
        documents_created['required'] = required_count

        _logger.info(f"=== DOCUMENT SERVICE COMPLETED ===")
        _logger.info(f"Created {documents_created['deliverable']} deliverable and {documents_created['required']} required documents")
        
        return documents_created

    def _create_deliverable_documents(self, project, deliverable_types):
        """Create deliverable documents for the project"""
        created_count = 0
        
        _logger.info(f"📦 Creating {len(deliverable_types)} deliverable document types")
        
        for i, doc_type in enumerate(deliverable_types):
            _logger.info(f"📄 Processing deliverable doc {i+1}/{len(deliverable_types)}: {doc_type}")
            
            if self._is_valid_document_type(doc_type):
                _logger.info(f"✅ Document type is valid")
                try:
                    # Get the product template from the document type
                    product_tmpl = self._get_product_template_from_doc_type(doc_type)
                    _logger.info(f"📦 Product template: {product_tmpl.name if product_tmpl else 'None'}")
                    
                    # Check for existing document line
                    has_existing = self.check_existing_documents(project, doc_type.document_type_id, product_tmpl)
                    if has_existing:
                        _logger.info(f"⚠️ Deliverable document line already exists, skipping: {doc_type.document_type_id.name}")
                        continue
                    
                    # Create deliverable document line
                    line_data = {
                        'project_id': project.id,
                        'product_tmpl_id': product_tmpl.id,
                        'document_type_id': doc_type.document_type_id.id,
                        'document_id': doc_type.document_id.id if hasattr(doc_type, 'document_id') and doc_type.document_id else False,
                        'is_required': doc_type.is_required if hasattr(doc_type, 'is_required') else False,
                    }
                    _logger.info(f"📝 Creating deliverable document line with data: {line_data}")
                    
                    document_line = self.env['project.document.type.line'].create(line_data)
                    _logger.info(f"✅ Created deliverable document line: {doc_type.document_type_id.name} (ID: {document_line.id})")
                    created_count += 1
                except Exception as e:
                    _logger.error(f"❌ Failed to create deliverable document {doc_type}: {e}")
                    import traceback
                    _logger.error(f"Full traceback: {traceback.format_exc()}")
            else:
                _logger.warning(f"⚠️ Document type is INVALID: {doc_type}")
                _logger.warning(f"   Has document_type_id: {hasattr(doc_type, 'document_type_id')}")
                if hasattr(doc_type, 'document_type_id'):
                    _logger.warning(f"   document_type_id value: {doc_type.document_type_id}")
                    _logger.warning(f"   document_type_id.id: {doc_type.document_type_id.id if doc_type.document_type_id else 'None'}")
        
        _logger.info(f"📦 Deliverable documents creation completed: {created_count} created")
        return created_count

    def _create_required_documents(self, project, required_types):
        """Create required documents for the project"""
        created_count = 0
        
        _logger.info(f"📋 Creating {len(required_types)} required document types")
        
        for i, doc_type in enumerate(required_types):
            _logger.info(f"📄 Processing required doc {i+1}/{len(required_types)}: {doc_type}")
            
            if self._is_valid_document_type(doc_type):
                _logger.info(f"✅ Document type is valid")
                try:
                    # Get the product template from the document type
                    product_tmpl = self._get_product_template_from_doc_type(doc_type)
                    _logger.info(f"📦 Product template: {product_tmpl.name if product_tmpl else 'None'}")
                    
                    # Check for existing document line
                    has_existing = self.check_existing_documents(project, doc_type.document_type_id, product_tmpl)
                    if has_existing:
                        _logger.info(f"⚠️ Required document line already exists, skipping: {doc_type.document_type_id.name}")
                        continue
                    
                    # Create required document line
                    line_data = {
                        'project_id': project.id,
                        'product_tmpl_id': product_tmpl.id,
                        'document_type_id': doc_type.document_type_id.id,
                        'document_id': doc_type.document_id.id if hasattr(doc_type, 'document_id') and doc_type.document_id else False,
                        'is_required': doc_type.is_required if hasattr(doc_type, 'is_required') else True,
                    }
                    _logger.info(f"📝 Creating required document line with data: {line_data}")
                    
                    document_line = self.env['project.document.required.line'].create(line_data)
                    _logger.info(f"✅ Created required document line: {doc_type.document_type_id.name} (ID: {document_line.id})")
                    created_count += 1
                except Exception as e:
                    _logger.error(f"❌ Failed to create required document {doc_type}: {e}")
                    import traceback
                    _logger.error(f"Full traceback: {traceback.format_exc()}")
            else:
                _logger.warning(f"⚠️ Document type is INVALID: {doc_type}")
                _logger.warning(f"   Has document_type_id: {hasattr(doc_type, 'document_type_id')}")
                if hasattr(doc_type, 'document_type_id'):
                    _logger.warning(f"   document_type_id value: {doc_type.document_type_id}")
                    _logger.warning(f"   document_type_id.id: {doc_type.document_type_id.id if doc_type.document_type_id else 'None'}")
        
        _logger.info(f"📋 Required documents creation completed: {created_count} created")
        return created_count

    def _is_valid_document_type(self, doc_type):
        """Check if document type is valid for creation"""
        return (
            hasattr(doc_type, 'document_type_id') and 
            doc_type.document_type_id and 
            doc_type.document_type_id.id
        )

    def _get_product_template_from_doc_type(self, doc_type):
        """Get product template from document type record"""
        if hasattr(doc_type, 'product_tmpl_id') and doc_type.product_tmpl_id:
            return doc_type.product_tmpl_id
        else:
            # Fallback: try to find from context or search
            _logger.warning(f"Could not get product template from doc_type {doc_type}")
            return self.env['product.template'] 