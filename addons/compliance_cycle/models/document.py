# -*- coding: utf-8 -*-

from odoo import models, fields, api


class ComplianceDocumentLines(models.Model):
    _name = 'compliance.document.lines'
    _description = 'Compliance Document Lines'
    _order = 'sequence'

    name = fields.Char(string='Document Name', required=True)
    sequence = fields.Integer(string='Sequence', default=10)
    compliance_id = fields.Many2one(
        'crm.lead',
        string='Compliance',
        ondelete='cascade'
    )
    document_type_id = fields.Many2one('project.document.type', string='Document Type', required=True)
    document_file = fields.Binary(string='Document File')
    document_filename = fields.Char(string='Document Filename')
    is_uploaded = fields.Boolean(string='Uploaded', default=False)
    is_verified = fields.Boolean(string='Verified', default=False)
    verification_date = fields.Date(string='Verification Date')
    verified_by = fields.Many2one('res.users', string='Verified By')
    notes = fields.Text(string='Notes')
    active = fields.Boolean(default=True, string='Active')

    @api.onchange('document_file')
    def _onchange_document_file(self):
        if self.document_file:
            self.is_uploaded = True
            self.is_verified = False
            self.verification_date = False
            self.verified_by = False

    def action_verify_document(self):
        self.ensure_one()
        self.write({
            'is_verified': True,
            'verification_date': fields.Date.today(),
            'verified_by': self.env.user.id
        })

    def action_unverify_document(self):
        self.ensure_one()
        self.write({
            'is_verified': False,
            'verification_date': False,
            'verified_by': False
        })

class TaskDocumentRequiredLines(models.Model):
    _inherit = 'task.document.required.lines'

    onboarding_id = fields.Many2one("initial.client.onboarding", string="Onboarding") 