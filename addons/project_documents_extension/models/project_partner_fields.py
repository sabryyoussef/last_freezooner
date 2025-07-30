# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
import logging

_logger = logging.getLogger(__name__)


class ProjectPartnerFields(models.Model):
    """
    Project Partner Fields Model
    Manages partner fields for projects with enhanced validation and update capabilities
    """
    _name = 'project.res.partner.fields'
    _description = 'Project Partner Fields'
    _order = 'id desc'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    # Basic Fields
    name = fields.Char(
        string='Name',
        compute='_compute_name',
        store=True,
        help='Name of the field record'
    )

    partner_id = fields.Many2one(
        'res.partner',
        related='project_id.partner_id',
        string='Partner',
        store=True,
        readonly=True,
        help='Related partner from the project'
    )

    project_id = fields.Many2one(
        'project.project',
        string='Project',
        required=True,
        ondelete='cascade'
    )

    field_id = fields.Many2one(
        'ir.model.fields',
        string='Field',
        domain="[('model','=', 'res.partner')]",
        required=True,
        ondelete='cascade',
        index=True,
        help='The partner field to manage'
    )

    field_name = fields.Char(
        string='Field Name',
        related='field_id.name',
        store=True,
        readonly=True,
        help='Technical name of the field'
    )

    is_required = fields.Boolean(
        string='Required',
        default=False,
        help='Whether this field is required for the project'
    )

    current_value = fields.Char(
        string="Current Value",
        compute='_compute_current_value',
        store=True,
        readonly=True,
        help="Current value of the field on the partner"
    )

    update_value = fields.Char(
        string="Update Value",
        help="New value to update the field to"
    )

    is_line_readonly = fields.Boolean(
        string="Line Readonly",
        default=False,
        help="Whether this line is readonly"
    )

    # Computed Methods
    @api.depends('field_id', 'project_id')
    def _compute_name(self):
        for record in self:
            if record.field_id and record.project_id:
                record.name = f"{record.project_id.name} - {record.field_id.field_description}"
            else:
                record.name = "Project Partner Field"

    @api.depends('field_id', 'partner_id')
    def _compute_current_value(self):
        for record in self:
            if record.field_id and record.partner_id:
                try:
                    field_name = record.field_id.name
                    if field_name and hasattr(record.partner_id, field_name):
                        value = getattr(record.partner_id, field_name, False)
                        if value:
                            # Handle different field types
                            if record.field_id.ttype in ['many2one']:
                                record.current_value = value.name if hasattr(value, 'name') else str(value)
                            elif record.field_id.ttype in ['selection']:
                                # Get selection label
                                selection = dict(record.partner_id._fields[field_name].selection)
                                record.current_value = selection.get(value, str(value))
                            else:
                                record.current_value = str(value)
                        else:
                            record.current_value = ''
                    else:
                        record.current_value = ''
                except Exception as e:
                    _logger.warning(f"Error computing current value for field {record.field_id.name}: {e}")
                    record.current_value = ''
            else:
                record.current_value = ''

    def action_update_field(self):
        """Update the partner field with the new value"""
        self.ensure_one()
        if not self.update_value:
            raise UserError(_("Please provide an update value"))
        
        if not self.partner_id:
            raise UserError(_("No partner found for this project"))
        
        try:
            field_name = self.field_id.name
            if hasattr(self.partner_id, field_name):
                setattr(self.partner_id, field_name, self.update_value)
                self.partner_id.message_post(
                    body=f"Field '{self.field_id.field_description}' updated via project '{self.project_id.name}'"
                )
                self._compute_current_value()  # Refresh current value
            else:
                raise UserError(_("Field not found on partner"))
        except Exception as e:
            raise UserError(_("Error updating field: %s") % str(e)) 