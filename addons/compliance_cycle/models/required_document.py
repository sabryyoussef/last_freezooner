# -*- coding: utf-8 -*-

from odoo import models, fields, api


class ComplianceRequiredDocument(models.Model):
    _name = 'compliance.required.document'
    _description = 'Compliance Required Document'
    _order = 'sequence'

    name = fields.Char(string='Document Name', required=True)
    sequence = fields.Integer(string='Sequence', default=10)
    is_required = fields.Boolean(string='Required', default=True)
    document_type = fields.Selection([
        ('passport', 'Passport'),
        ('visa', 'Visa'),
        ('license', 'License'),
        ('other', 'Other')
    ], string='Document Type', required=True)
    description = fields.Text(string='Description')
    active = fields.Boolean(default=True, string='Active') 