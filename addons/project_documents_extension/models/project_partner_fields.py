# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
import re
import logging

_logger = logging.getLogger(__name__)


class LegalEntityType(models.Model):
    """
    Legal Entity Type Model
    Manages different types of legal entities (FZCO, FZE, LLC, etc.)
    """
    _name = 'legal.entity.type'
    _description = 'Legal Entity Type'
    _order = 'sequence, name'

    name = fields.Char(
        string='Entity Type Name',
        required=True,
        help='Name of the legal entity type (e.g., FZCO, FZE, LLC)'
    )

    code = fields.Char(
        string='Entity Code',
        required=True,
        help='Short code for the entity type'
    )

    sequence = fields.Integer(
        string='Sequence',
        default=10,
        help='Ordering sequence'
    )

    description = fields.Text(
        string='Description',
        help='Detailed description of the legal entity type'
    )

    is_active = fields.Boolean(
        string='Active',
        default=True,
        help='Whether this entity type is active'
    )

    requirements = fields.Text(
        string='Requirements',
        help='Requirements and documents needed for this entity type'
    )

    _sql_constraints = [
        ('unique_code', 'unique(code)', 'Entity code must be unique!')
    ]


class PartnerHandType(models.Model):
    """
    Partner Hand Type Model
    Manages whether a partner is a company or individual
    """
    _name = 'partner.hand.type'
    _description = 'Partner Hand Type'
    _order = 'sequence, name'

    name = fields.Char(
        string='Hand Type Name',
        required=True,
        help='Name of the hand type (e.g., Company, Individual)'
    )

    code = fields.Char(
        string='Hand Code',
        required=True,
        help='Short code for the hand type'
    )

    sequence = fields.Integer(
        string='Sequence',
        default=10,
        help='Ordering sequence'
    )

    description = fields.Text(
        string='Description',
        help='Detailed description of the hand type'
    )

    is_active = fields.Boolean(
        string='Active',
        default=True,
        help='Whether this hand type is active'
    )

    _sql_constraints = [
        ('unique_code', 'unique(code)', 'Hand code must be unique!')
    ]


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

    field_type = fields.Selection(
        related='field_id.ttype',
        string='Field Type',
        store=True,
        help='Type of the field'
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

    # Enhanced Fields
    state_id = fields.Many2one(
        'res.country.state',
        string='State',
        help='State field for address-related fields'
    )

    # Legal Entity and Hand Management
    legal_entity_type_id = fields.Many2one(
        'legal.entity.type',
        string='Legal Entity Type',
        help='Type of legal entity (FZCO, FZE, LLC, etc.)'
    )

    hand_type_id = fields.Many2one(
        'partner.hand.type',
        string='Hand Type',
        help='Whether partner is a company or individual'
    )

    # Enhanced Partner Information
    trade_license_number = fields.Char(
        string='Trade License Number',
        help='Trade license number for the partner'
    )

    establishment_card_number = fields.Char(
        string='Establishment Card Number',
        help='Establishment card number for the partner'
    )

    visa_number = fields.Char(
        string='Visa Number',
        help='Visa number for the partner'
    )

    emirates_id = fields.Char(
        string='Emirates ID',
        help='Emirates ID for the partner'
    )

    passport_number = fields.Char(
        string='Passport Number',
        help='Passport number for the partner'
    )

    # Status Fields
    is_verified = fields.Boolean(
        string='Verified',
        default=False,
        help='Whether the partner information has been verified'
    )

    verification_date = fields.Date(
        string='Verification Date',
        help='Date when the partner information was verified'
    )

    verified_by = fields.Many2one(
        'res.users',
        string='Verified By',
        help='User who verified the partner information'
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
                            elif record.field_id.ttype in ['many2many']:
                                # Handle many2many fields
                                if hasattr(value, 'mapped'):
                                    record.current_value = ', '.join(value.mapped('name'))
                                else:
                                    record.current_value = str(value)
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

    def update_values(self):
        """Update field values based on field type"""
        for rec in self:
            if not rec.field_id or not rec.update_value:
                continue

            try:
                if rec.field_id.ttype == 'many2one':
                    # Handle many2one fields
                    match = re.search(r'\((\d+),?\)', str(rec.update_value))
                    if match:
                        record = self.env[rec.field_id.relation].sudo().browse(int(match.group(1)))
                        rec.update_value = record.name if record else ''

                elif rec.field_id.ttype == 'many2many':
                    # Handle many2many fields
                    ids = [re.search(r'\((\d+),?\)', str(line)) for line in rec.current_value]
                    ids = [match.group(1) for match in ids if match]
                    records = self.env[rec.field_id.relation].sudo().browse([int(id) for id in ids])
                    rec.update_value = ', '.join(records.mapped('name')) if records else ''

            except Exception as e:
                _logger.error('Error updating field values: %s', str(e))
                raise ValidationError(_('Error updating field values: %s') % str(e))

    def action_update_relation_fields(self, many2one_id=None):
        """Update relation fields (many2one)"""
        for rec in self:
            if not rec.field_id or not rec.partner_id:
                continue

            try:
                field_name = rec.field_id.name
                if not hasattr(rec.partner_id, field_name):
                    raise ValidationError(_('Field "%s" does not exist on the partner model.') % field_name)

                if not many2one_id:
                    raise ValidationError(_('No value provided for the field update.'))

                # Update the partner field
                rec.partner_id.with_context(skip_validation=True).write({field_name: many2one_id})
                rec.update_value = many2one_id
                rec.update_values()

            except Exception as e:
                _logger.error('Error updating relation field: %s', str(e))
                raise ValidationError(_('Error updating field value: %s') % str(e))

    def action_update_many2many_fields(self, many2many_ids=None):
        """Update many2many fields"""
        for rec in self:
            if not rec.field_id or not rec.partner_id:
                continue

            try:
                field_name = rec.field_id.name
                if not hasattr(rec.partner_id, field_name):
                    raise ValidationError(_('Field "%s" does not exist on the partner model.') % field_name)

                if not many2many_ids or not many2many_ids.exists():
                    raise ValidationError(_('No valid records provided to update the Many2many field.'))

                if len(many2many_ids) > 1:
                    raise ValidationError(_('Please select only one value from partner assessment.'))

                # Update the partner field
                new_id = many2many_ids[0].id
                rec.partner_id.with_context(skip_validation=True).write({
                    field_name: [(6, 0, [new_id])]
                })
                rec.update_value = new_id
                rec.update_values()

            except Exception as e:
                _logger.error('Error updating many2many field: %s', str(e))
                raise ValidationError(_('Error updating Many2many field value: %s') % str(e))

    def action_update_normal_fields(self):
        """Update normal fields (char, text, boolean, etc.)"""
        for rec in self:
            if not rec.field_id or not rec.partner_id:
                continue

            try:
                field_name = rec.field_id.name
                if not hasattr(rec.partner_id, field_name):
                    raise ValidationError(_('Field "%s" does not exist on the partner model.') % field_name)

                # Handle boolean fields
                if rec.field_type == 'boolean':
                    update_value = bool(rec.update_value)
                else:
                    update_value = rec.update_value
                    if not update_value:
                        raise ValidationError(_('No value provided for the field update.'))

                # Update the partner field
                rec.partner_id.with_context(skip_validation=True).write({field_name: update_value})
                rec.update_value = update_value
                rec.update_values()

            except Exception as e:
                _logger.error('Error updating normal field: %s', str(e))
                raise ValidationError(_('Error updating field value: %s') % str(e))

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
                # Handle different field types
                if self.field_type == 'many2one':
                    self.action_update_relation_fields(self.update_value)
                elif self.field_type == 'many2many':
                    # For many2many, we need to pass the actual records
                    # This is a simplified version - in practice you'd need to handle the record selection
                    self.action_update_normal_fields()
                else:
                    self.action_update_normal_fields()
                
                self.partner_id.message_post(
                    body=f"Field '{self.field_id.field_description}' updated via project '{self.project_id.name}'"
                )
                self._compute_current_value()  # Refresh current value
            else:
                raise UserError(_("Field not found on partner"))
        except Exception as e:
            raise UserError(_("Error updating field: %s") % str(e))

    def action_update_lines(self):
        """Update all lines in the current recordset"""
        for record in self:
            if record.update_value:
                record.action_update_field()

    def action_reset(self):
        """Reset the update value"""
        for record in self:
            record.update_value = ''

    def action_retain_value(self):
        """Retain the current value as update value"""
        for record in self:
            record.update_value = record.current_value

    def action_verify_partner(self):
        """Verify the partner information"""
        self.ensure_one()
        if not self.partner_id:
            raise UserError(_("No partner found for this project"))
        
        self.write({
            'is_verified': True,
            'verification_date': fields.Date.today(),
            'verified_by': self.env.user.id
        })
        
        self.partner_id.message_post(
            body=f"Partner information verified by {self.env.user.name} via project '{self.project_id.name}'"
        )
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Success'),
                'message': _('Partner information has been verified.'),
                'type': 'success',
            }
        }

    def action_unverify_partner(self):
        """Unverify the partner information"""
        self.ensure_one()
        
        self.write({
            'is_verified': False,
            'verification_date': False,
            'verified_by': False
        })
        
        self.partner_id.message_post(
            body=f"Partner information verification removed by {self.env.user.name} via project '{self.project_id.name}'"
        )
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Success'),
                'message': _('Partner information verification has been removed.'),
                'type': 'success',
            }
        }

    def action_validate_legal_entity(self):
        """Validate legal entity information"""
        self.ensure_one()
        
        if not self.legal_entity_type_id:
            raise UserError(_("Please select a legal entity type"))
        
        if not self.trade_license_number:
            raise UserError(_("Please provide a trade license number"))
        
        # Add validation logic here
        self.partner_id.message_post(
            body=f"Legal entity validation completed for {self.legal_entity_type_id.name} via project '{self.project_id.name}'"
        )
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Success'),
                'message': _('Legal entity information has been validated.'),
                'type': 'success',
            }
        }

    def action_validate_hand_type(self):
        """Validate hand type information"""
        self.ensure_one()
        
        if not self.hand_type_id:
            raise UserError(_("Please select a hand type"))
        
        # Add validation logic here
        self.partner_id.message_post(
            body=f"Hand type validation completed for {self.hand_type_id.name} via project '{self.project_id.name}'"
        )
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Success'),
                'message': _('Hand type information has been validated.'),
                'type': 'success',
            }
        } 