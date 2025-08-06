from odoo import models, api, fields

class ProductTemplate(models.Model):
    _inherit = 'product.template'

    service_tracking = fields.Selection(
        [
            ("no", "No"),
            ("manual", "Manual"),
            ("automatic", "Automatic"),
            ("new_workflow", "New Workflow"),
            ("project_only", "Project Only"),
            ("task_in_project", "Task in Project"),
            ("task_global_project", "Task in Global Project"),
        ],
        string="Service Tracking",
        default="manual",
        tracking=True,
        help="How to track service delivery",
    )

    task_template_ids = fields.One2many(
        'product.task.template',
        'product_tmpl_id',
        string='Task Templates',
        help='Task templates that will be created when this product is added to a project'
    )

    # Comment out legacy field definition
    # document_type_ids = fields.One2many(
    #     'project.document.type.line', 'product_tmpl_id', string='Deliverable Document Types'
    # )

    x_required_document_ids = fields.One2many(
        'project.required.document', 'product_tmpl_id', string='x_Required Documents'
    )
    x_deliverable_document_ids = fields.One2many(
        'project.deliverable.document', 'product_tmpl_id', string='x_Deliverable Documents'
    )

    @api.model_create_multi
    def create(self, vals_list):
        templates = super().create(vals_list)
        for template in templates:
            if template.service_tracking == 'new_workflow' and not template.task_template_ids:
                template._create_default_task_templates()
        return templates

    def write(self, vals):
        result = super().write(vals)
        if vals.get('service_tracking') == 'new_workflow':
            for template in self:
                if not template.task_template_ids:
                    template._create_default_task_templates()
        return result

    def _create_default_task_templates(self):
        if self.service_tracking != 'new_workflow':
            return
        default_templates = [
            {'name': 'Document Collection', 'description': 'Collect all required documents from the client', 'sequence': 10, 'planned_hours': 2.0},
            {'name': 'Document Review', 'description': 'Review and validate all submitted documents', 'sequence': 20, 'planned_hours': 1.0},
            {'name': 'Process Completion', 'description': 'Complete the process and deliver results', 'sequence': 30, 'planned_hours': 1.0},
        ]
        for template_data in default_templates:
            template_data['product_tmpl_id'] = self.id
            self.env['product.task.template'].create(template_data)
    
    def action_select_existing_task_template(self):
        """Action to select from existing task templates when adding a line"""
        return {
            'name': 'Select Existing Task Template',
            'type': 'ir.actions.act_window',
            'res_model': 'select.task.template.wizard',
            'view_mode': 'form',
            'context': {
                'default_product_tmpl_id': self.id,
            },
            'target': 'new'
        }

class ProductProduct(models.Model):
    _inherit = 'product.product'

    service_tracking = fields.Selection(
        related="product_tmpl_id.service_tracking",
        store=True,
        readonly=False,
    )

class ProjectDocumentTypeLine(models.Model):
    _inherit = 'project.document.type.line'
    product_tmpl_id = fields.Many2one('product.template', string='Product Template', ondelete='cascade')

class ProjectDocumentRequiredLine(models.Model):
    _inherit = 'project.document.required.line'
    product_tmpl_id = fields.Many2one('product.template', string='Product Template', ondelete='cascade') 