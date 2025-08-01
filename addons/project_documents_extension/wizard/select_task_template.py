from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
import logging

_logger = logging.getLogger(__name__)


class SelectTaskTemplateWizard(models.TransientModel):
    """
    Wizard for selecting existing task templates
    """
    _name = 'select.task.template.wizard'
    _description = 'Select Task Template Wizard'

    # Fields
    product_tmpl_id = fields.Many2one(
        'product.template',
        string='Product Template',
        required=True,
        help='Product template to filter task templates'
    )
    
    selected_task_template_ids = fields.Many2many(
        'product.task.template',
        'select_wizard_selected_templates_rel',
        'wizard_id',
        'template_id',
        string='Selected Task Templates',
        domain="[('product_tmpl_id', '=', product_tmpl_id)]",
        help='Task templates that will be added to the product'
    )
    
    # Context fields
    parent_product_tmpl_id = fields.Many2one(
        'product.template',
        string='Parent Product Template',
        help='Product template from which this wizard was called'
    )
    
    @api.model
    def default_get(self, fields_list):
        """Set default values based on context"""
        defaults = super().default_get(fields_list)
        
        # Get product template from context
        product_tmpl_id = self.env.context.get('default_product_tmpl_id')
        if product_tmpl_id:
            defaults['product_tmpl_id'] = product_tmpl_id
            defaults['parent_product_tmpl_id'] = product_tmpl_id
        
        return defaults
    
    def action_select_templates(self):
        """Action to select task templates and add them to the product"""
        self.ensure_one()
        
        if not self.selected_task_template_ids:
            raise ValidationError(_("Please select at least one task template."))
        
        # Get the parent product template
        product_tmpl = self.parent_product_tmpl_id or self.product_tmpl_id
        
        if not product_tmpl:
            raise ValidationError(_("Product template not found."))
        
        # Add selected templates to the product
        for template in self.selected_task_template_ids:
            # Check if template is already in the product
            existing = product_tmpl.task_template_ids.filtered(
                lambda t: t.id == template.id
            )
            if not existing:
                # Create a copy of the template for this product
                new_template_vals = {
                    'name': template.name,
                    'product_tmpl_id': product_tmpl.id,
                    'description': template.description,
                    'user_ids': [(6, 0, template.user_ids.ids)],
                    'stage_id': template.stage_id.id,
                    'planned_hours': template.planned_hours,
                    'priority': template.priority,
                    'sequence': template.sequence,
                    'checkpoint_field': template.checkpoint_field,
                    'milestone_message': template.milestone_message,
                }
                
                new_template = self.env['product.task.template'].create(new_template_vals)
                
                # Copy subtasks
                for subtask in template.subtask_ids:
                    subtask_vals = {
                        'name': subtask.name,
                        'task_template_id': new_template.id,
                        'description': subtask.description,
                        'user_ids': [(6, 0, subtask.user_ids.ids)],
                        'stage_id': subtask.stage_id.id,
                        'planned_hours': subtask.planned_hours,
                        'priority': subtask.priority,
                        'sequence': subtask.sequence,
                        'milestone_message': subtask.milestone_message,
                    }
                    self.env['product.subtask.template'].create(subtask_vals)
                
                _logger.info(f"Added task template '{template.name}' to product '{product_tmpl.name}'")
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Success'),
                'message': _('Selected task templates have been added to the product.'),
                'type': 'success',
                'sticky': False,
            }
        }
    
    def action_create_new_template(self):
        """Action to create a new task template"""
        return {
            'name': _('Create New Task Template'),
            'type': 'ir.actions.act_window',
            'res_model': 'product.task.template',
            'view_mode': 'form',
            'context': {
                'default_product_tmpl_id': self.product_tmpl_id.id,
            },
            'target': 'new'
        } 