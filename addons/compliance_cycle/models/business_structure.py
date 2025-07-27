# -*- coding: utf-8 -*-

from odoo import models, fields, api


class ResPartnerBusinessStructure(models.Model):
    _name = 'res.partner.business.structure'
    _description = 'Business Structure'
    _order = 'name'

    name = fields.Char(string='Structure Name', required=True)
    code = fields.Char(string='Code', required=True)
    description = fields.Text(string='Description')
    active = fields.Boolean(default=True, string='Active')

    # Partner count
    partner_count = fields.Integer(
        string='Partners',
        compute='_compute_partner_count'
    )

    @api.depends('name')
    def _compute_partner_count(self):
        """Compute the number of partners using this business structure"""
        for record in self:
            record.partner_count = self.env['res.partner'].search_count([
                ('business_structure_id', '=', record.id)
            ])


class ResPartnerBusinessShareholder(models.Model):
    _name = 'res.partner.business.shareholder'
    _description = 'Business Shareholder'
    _order = 'name'

    name = fields.Char(string='Shareholder Name', required=True)
    partner_id = fields.Many2one(
        'res.partner',
        string='Partner',
        required=True,
        ondelete='cascade'
    )
    contact_id = fields.Many2one(
        'res.partner',
        string='Contact Person',
        domain="[('is_company', '=', False)]"
    )
    ubo_id = fields.Many2one(
        'res.partner',
        string='Ultimate Beneficial Owner',
        domain="[('is_company', '=', False)]"
    )
    shareholding = fields.Float(
        string='Shareholding (%)',
        help='Percentage of shares owned'
    )
    relationship_ids = fields.Many2many(
        'res.partner.relationship',
        string='Relationships',
        help='Relationships with other shareholders'
    )
    notes = fields.Text(string='Notes')


class ResPartnerAddress(models.Model):
    _name = 'res.partner.address'
    _description = 'Partner Address'
    _order = 'type, name'

    name = fields.Char(string='Address Name', required=True)
    partner_id = fields.Many2one(
        'res.partner',
        string='Partner',
        required=True,
        ondelete='cascade'
    )
    type = fields.Selection([
        ('home', 'Home'),
        ('work', 'Work'),
        ('billing', 'Billing'),
        ('shipping', 'Shipping'),
        ('other', 'Other')
    ], string='Address Type', required=True, default='work')
    
    street = fields.Char(string='Street')
    street2 = fields.Char(string='Street 2')
    zip = fields.Char(string='ZIP')
    city = fields.Char(string='City')
    state_id = fields.Many2one(
        'res.country.state',
        string='State'
    )
    country_id = fields.Many2one(
        'res.country',
        string='Country'
    )
    is_primary = fields.Boolean(
        string='Primary Address',
        default=False
    )
    active = fields.Boolean(default=True, string='Active')


class ResPartnerRelationship(models.Model):
    _name = 'res.partner.relationship'
    _description = 'Partner Relationship'
    _order = 'name'

    name = fields.Char(string='Relationship Type', required=True)
    code = fields.Char(string='Code')
    description = fields.Text(string='Description')
    active = fields.Boolean(default=True, string='Active')


class ProjectProjectProducts(models.Model):
    _name = 'project.project.products'
    _description = 'Project Products'
    _order = 'name'

    name = fields.Char(string='Product Name', required=True)
    partner_id = fields.Many2one(
        'res.partner',
        string='Partner',
        required=True,
        ondelete='cascade'
    )
    product_id = fields.Many2one(
        'product.product',
        string='Product',
        required=True
    )
    quantity = fields.Float(string='Quantity', default=1.0)
    unit_price = fields.Float(string='Unit Price')
    total_price = fields.Float(
        string='Total Price',
        compute='_compute_total_price',
        store=True
    )
    notes = fields.Text(string='Notes')

    @api.depends('quantity', 'unit_price')
    def _compute_total_price(self):
        """Compute total price based on quantity and unit price"""
        for record in self:
            record.total_price = record.quantity * record.unit_price 