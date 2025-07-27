# -*- coding: utf-8 -*-

from odoo import models, fields, api


class ComplianceCountry(models.Model):
    _inherit = 'res.country'

    is_compliance_required = fields.Boolean(
        string='Compliance Required',
        default=False,
        help='Check if compliance is required for this country'
    )
    compliance_documents = fields.Text(
        string='Required Documents',
        help='List of required documents for compliance in this country'
    )
    compliance_notes = fields.Text(
        string='Compliance Notes',
        help='Additional notes for compliance in this country'
    )
    risk_level = fields.Selection([
        ('low', 'Low Risk'),
        ('medium', 'Medium Risk'),
        ('high', 'High Risk'),
        ('very_high', 'Very High Risk')
    ], string='Risk Level', default='low') 