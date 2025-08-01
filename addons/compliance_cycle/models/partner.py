# -*- coding: utf-8 -*-

from odoo import models, fields, api


class ResPartner(models.Model):
    _inherit = 'res.partner'

    # Business Structure Fields
    business_structure_id = fields.Many2one(
        'res.partner.business.structure',
        string='Business Structure',
        help='Type of business structure'
    )
    nationality_id = fields.Many2one(
        'res.country',
        string='Nationality',
        help='Nationality for individual partners'
    )

    # Address Management
    partner_address_lines = fields.One2many(
        'res.partner.address',
        'partner_id',
        string='Address Lines',
        help='Multiple addresses for the partner'
    )

    # Shareholder Compliance
    compliance_shareholder_ids = fields.One2many(
        'res.partner.business.shareholder',
        'partner_id',
        string='Compliance Shareholders',
        help='Shareholder information for compliance'
    )

    # Project Products
    project_product_ids = fields.One2many(
        'project.project.products',
        'partner_id',
        string='Project Products',
        help='Products associated with projects for this partner'
    )

    # Compliance Status
    compliance_status = fields.Selection([
        ('pending', 'Pending'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('rejected', 'Rejected')
    ], string='Compliance Status', default='pending', tracking=True)

    # Compliance Notes
    compliance_notes = fields.Text(
        string='Compliance Notes',
        help='Additional notes for compliance process'
    )

    @api.onchange('company_type')
    def _onchange_company_type(self):
        """Handle company type changes for compliance fields"""
        if self.company_type == 'person':
            self.business_structure_id = False
        else:
            self.nationality_id = False 