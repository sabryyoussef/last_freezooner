from odoo import models, fields, api
from collections import defaultdict
from ..services.project_document_service import copy_documents_from_product_to_project, copy_documents_from_project_to_task
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError

class ProjectDocumentCategory(models.Model):
    _name = 'project.document.category'
    _description = 'Project Document Category'
    _rec_name = 'name'

    name = fields.Char('Category Name', required=True)
    description = fields.Text('Description')
    document_type_ids = fields.One2many('project.document.type', 'category_id', string='Document Types')

class ProjectDocumentType(models.Model):
    _name = 'project.document.type'
    _description = 'Project Document Type'

    name = fields.Char('Type Name', required=True)
    category_id = fields.Many2one('project.document.category', string='Category')
    description = fields.Text('Description')
    is_required = fields.Boolean('Required', default=False)
    expiry_required = fields.Boolean('Expiry Required', default=False)
    reminder_days = fields.Integer('Reminder Days', default=30, help='Days before expiry to send reminder')
    document_ids = fields.One2many('project.document.type.line', 'document_type_id', string='Document Lines')

class ProjectDocumentTypeLine(models.Model):
    _name = 'project.document.type.line'
    _description = 'Project Deliverable Document Type Line'

    project_id = fields.Many2one('project.project', string='Project', ondelete='cascade')
    task_id = fields.Many2one('project.task', string='Task', ondelete='cascade')
    document_type_id = fields.Many2one('project.document.type', string='Document Type', required=True)
    document_id = fields.Many2one('documents.document', string='Document Type', required=True)
    is_required = fields.Boolean(string='Required', default=False)
    expiry_date = fields.Date('Expiry Date')
    reminder_days = fields.Integer('Reminder Days', default=30)
    is_expired = fields.Boolean('Is Expired', compute='_compute_expired', store=True)
    is_verify = fields.Boolean('Is Verified', default=False)
    number = fields.Char(
        string="Number",
        required=True,
        copy=False,
        readonly=True,
        index=True,
        default=lambda self: _("New"),
    )
    issue_date = fields.Date(
        default=fields.Date.today,
        help="Date when the document was issued",
    )
    attachment_ids = fields.Many2many('ir.attachment', string='Attachments')
    expiration_reminder = fields.Boolean(default=False)
    expiration_reminder_sent = fields.Boolean(default=False)
    document_create_date = fields.Datetime(
        readonly=True,
        string="Document Create Date",
        default=fields.datetime.now(),
    )

    @api.depends('expiry_date')
    def _compute_expired(self):
        for record in self:
            record.is_expired = record.expiry_date and record.expiry_date < fields.Date.today()

    def action_numbers(self):
        docs = self.env['project.document.type.line'].sudo().search([])
        for doc in docs:
            doc.number = self.env['ir.sequence'].next_by_code('project.document.type.line') or _("New")

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if 'number' not in vals:
                vals['number'] = self.env['ir.sequence'].next_by_code('project.document.type.line') or _("New")
        return super(ProjectDocumentTypeLine, self).create(vals_list)

    # @api.constrains('project_id', 'task_id', 'issue_date', 'document_type_id')
    # def check_duplicate_document(self):
    #     if self.env.context.get('bypass_duplicate_check'):
    #         return
    #     for rec in self:
    #         domain = [
    #             ('document_type_id', '=', rec.document_type_id.id),
    #             ('issue_date', '=', rec.issue_date),
    #             ('id', '!=', rec.id),
    #         ]
    #         if rec.project_id:
    #             domain.append(('project_id', '=', rec.project_id.id))
    #         if rec.task_id:
    #             domain.append(('task_id', '=', rec.task_id.id))
    #         
    #         duplicate_document = self.search(domain)
    #         if duplicate_document:
    #             raise ValidationError(_("This document already exists!"))

    def write(self, vals):
        res = super(ProjectDocumentTypeLine, self).write(vals)
        if vals.get('expiry_date'):
            self.write({'expiration_reminder_sent': False})
        if vals.get('attachment_ids'):
            self.write({'document_create_date': fields.Datetime.today()})
        return res

    def action_upload_document(self):
        """Action to upload document for this line"""
        self.ensure_one()
        return {
            'name': _('Upload Document'),
            'type': 'ir.actions.act_window',
            'res_model': 'document.upload.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_name': self.document_type_id.name,
                'default_document_type': 'deliverable' if self.project_id else 'required',
                'default_project_id': self.project_id.id if self.project_id else False,
                'default_task_id': self.task_id.id if self.task_id else False,
                'default_document_line_id': self.id,
            }
        }

class ProjectDocumentRequiredLine(models.Model):
    _name = 'project.document.required.line'
    _description = 'Project Required Document Type Line'

    project_id = fields.Many2one('project.project', string='Project', ondelete='cascade')
    task_id = fields.Many2one('project.task', string='Task', ondelete='cascade')
    document_type_id = fields.Many2one('project.document.type', string='Document Type', required=True)
    document_id = fields.Many2one('documents.document', string='Document Type', required=True)
    is_required = fields.Boolean(string='Required', default=False)
    expiry_date = fields.Date('Expiry Date')
    reminder_days = fields.Integer('Reminder Days', default=30)
    is_expired = fields.Boolean('Is Expired', compute='_compute_expired', store=True)
    is_verify = fields.Boolean('Is Verified', default=False)
    number = fields.Char(
        string="Number",
        required=True,
        copy=False,
        readonly=True,
        index=True,
        default=lambda self: _("New"),
    )
    issue_date = fields.Date(
        default=fields.Date.today,
        help="Date when the document was issued",
    )
    attachment_ids = fields.Many2many('ir.attachment', string='Attachments')
    expiration_reminder = fields.Boolean(default=False)
    expiration_reminder_sent = fields.Boolean(default=False)
    document_create_date = fields.Datetime(
        readonly=True,
        string="Document Create Date",
        default=fields.datetime.now(),
    )

    @api.depends('expiry_date')
    def _compute_expired(self):
        for record in self:
            record.is_expired = record.expiry_date and record.expiry_date < fields.Date.today()

    def action_numbers(self):
        docs = self.env['project.document.required.line'].sudo().search([])
        for doc in docs:
            doc.number = self.env['ir.sequence'].next_by_code('project.document.required.line') or _("New")

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if 'number' not in vals:
                vals['number'] = self.env['ir.sequence'].next_by_code('project.document.required.line') or _("New")
        return super(ProjectDocumentRequiredLine, self).create(vals_list)

    # @api.constrains('project_id', 'task_id', 'issue_date', 'document_type_id')
    # def check_duplicate_document(self):
    #     if self.env.context.get('bypass_duplicate_check'):
    #         return
    #     for rec in self:
    #         domain = [
    #             ('document_type_id', '=', rec.document_type_id.id),
    #             ('issue_date', '=', rec.issue_date),
    #             ('id', '!=', rec.id),
    #         ]
    #         if rec.project_id:
    #             domain.append(('project_id', '=', rec.project_id.id))
    #         if rec.task_id:
    #             domain.append(('task_id', '=', rec.task_id.id))
    #         
    #         duplicate_document = self.search(domain)
    #         if duplicate_document:
    #             raise ValidationError(_("This document already exists!"))

    def write(self, vals):
        res = super(ProjectDocumentRequiredLine, self).write(vals)
        if vals.get('expiry_date'):
            self.write({'expiration_reminder_sent': False})
        if vals.get('attachment_ids'):
            self.write({'document_create_date': fields.Datetime.today()})
        return res

    def action_upload_document(self):
        """Action to upload document for this line"""
        self.ensure_one()
        return {
            'name': _('Upload Document'),
            'type': 'ir.actions.act_window',
            'res_model': 'document.upload.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_name': self.document_type_id.name,
                'default_document_type': 'required',
                'default_project_id': self.project_id.id if self.project_id else False,
                'default_task_id': self.task_id.id if self.task_id else False,
                'default_document_line_id': self.id,
            }
        }

class ProjectProject(models.Model):
    _inherit = 'project.project'

    document_type_ids = fields.One2many(
        'project.document.type.line', 'project_id', string='Deliverable Document Types')
    document_required_type_ids = fields.One2many(
        'project.document.required.line', 'project_id', string='Required Document Types')
    # sale_order_id field is inherited from sale_project, do not redefine

    # --- Workflow checkboxes for Required Documents ---
    required_document_complete = fields.Boolean(string="Required Document Complete", default=False)
    required_document_confirm = fields.Boolean(string="Required Document Confirm", default=False)
    required_document_update = fields.Boolean(string="Required Document Update", default=False)

    # --- Workflow checkboxes for Deliverable Documents ---
    deliverable_document_complete = fields.Boolean(string="Deliverable Document Complete", default=False)
    deliverable_document_confirm = fields.Boolean(string="Deliverable Document Confirm", default=False)
    deliverable_document_update = fields.Boolean(string="Deliverable Document Update", default=False)

    # --- Project-specific fields ---
    return_reason = fields.Text(string="Return Reason")
    return_date = fields.Date(string="Return Date")
    update_reason = fields.Text(string="Update Reason")
    update_date = fields.Date(string="Update Date")

    @api.model_create_multi
    def create(self, vals_list):
        projects = super().create(vals_list)
        for project in projects:
            # Try to get product templates from sale order lines if available
            sale_line_id = project.sale_line_id.id if hasattr(project, 'sale_line_id') and project.sale_line_id else None
            product_templates = []
            if sale_line_id:
                sale_line = self.env['sale.order.line'].browse(sale_line_id)
                if sale_line and sale_line.product_id:
                    product_templates.append(sale_line.product_id.product_tmpl_id)
            # Optionally, add logic to get product templates from context if needed
            if product_templates:
                copy_documents_from_product_to_project(self.env, project, product_templates)
        return projects

    # --- Project-level document management methods ---
    def action_complete_required_documents(self):
        """Complete required documents for project"""
        self.ensure_one()
        self.required_document_complete = True
        return True

    def action_confirm_required_documents(self):
        """Confirm required documents for project"""
        self.ensure_one()
        self.required_document_confirm = True
        return True

    def action_update_required_documents(self):
        """Update required documents for project"""
        self.ensure_one()
        self.required_document_update = True
        return True

    def action_reset_required_document_complete(self):
        """Reset required document complete status"""
        self.ensure_one()
        self.required_document_complete = False
        return True

    def action_reset_required_document_confirm(self):
        """Reset required document confirm status"""
        self.ensure_one()
        self.required_document_confirm = False
        return True

    def action_reset_required_document_update(self):
        """Reset required document update status"""
        self.ensure_one()
        self.required_document_update = False
        return True

    def action_complete_deliverable_documents(self):
        """Complete deliverable documents for project"""
        self.ensure_one()
        self.deliverable_document_complete = True
        return True

    def action_confirm_deliverable_documents(self):
        """Confirm deliverable documents for project"""
        self.ensure_one()
        self.deliverable_document_confirm = True
        return True

    def action_update_deliverable_documents(self):
        """Update deliverable documents for project"""
        self.ensure_one()
        self.deliverable_document_update = True
        return True

    def action_reset_deliverable_document_complete(self):
        """Reset deliverable document complete status"""
        self.ensure_one()
        self.deliverable_document_complete = False
        return True

    def action_reset_deliverable_document_confirm(self):
        """Reset deliverable document confirm status"""
        self.ensure_one()
        self.deliverable_document_confirm = False
        return True

    def action_reset_deliverable_document_update(self):
        """Reset deliverable document update status"""
        self.ensure_one()
        self.deliverable_document_update = False
        return True

class ProjectTask(models.Model):
    _inherit = 'project.task'

    document_required_type_ids = fields.One2many(
        'project.document.required.line', 'task_id', string='Required Document Types')
    document_type_ids = fields.One2many(
        'project.document.type.line', 'task_id', string='Deliverable Document Types')

    @api.model_create_multi
    def create(self, vals_list):
        tasks = super().create(vals_list)
        for task in tasks:
            project = task.project_id
            if project:
                copy_documents_from_project_to_task(task.env, task, project)
        return tasks

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    project_ids = fields.Many2many('project.project', compute='_compute_project_ids', string='Projects', store=False)
    project_count = fields.Integer(string='Number of Projects', compute='_compute_project_ids', store=False)

    def _compute_project_ids(self):
        is_project_manager = self.env.user.has_group('project.group_project_manager')
        projects = self.env['project.project'].search([
            ('sale_order_id', 'in', self.ids)
        ])
        projects_per_so = defaultdict(lambda: self.env['project.project'])
        for project in projects:
            projects_per_so[project.sale_order_id.id] |= project

        for order in self:
            # Fetch projects from various sources
            projects = order.order_line.mapped('product_id.project_id')
            projects |= order.order_line.mapped('project_id')
            projects |= projects_per_so[order.id or order._origin.id]
            # Restrict projects if user is not a project manager
            if not is_project_manager:
                projects = projects._filter_access_rules('read')
            order.project_ids = projects
            order.project_count = len(projects)

    def action_confirm(self):
        res = super().action_confirm()
        self._create_tasks_from_templates()
        return res

    def _create_tasks_from_templates(self):
        for order in self:
            all_workflow_products = order.order_line.mapped('product_id').filtered(
                lambda p: p.service_tracking == 'new_workflow'
            )
            products_with_templates = all_workflow_products.filtered(
                lambda p: p.product_tmpl_id.task_template_ids
            )
            if not all_workflow_products:
                continue
            # Find or create project for this order
            # Fix: Use sale_line_id.order_id instead of sale_order_id
            projects = self.env['project.project'].search([('sale_line_id.order_id', '=', order.id)])
            if not projects:
                # Pass context for document propagation
                ctx = self.env.context.copy()
                if order.order_line:
                    ctx['default_sale_order_line_id'] = order.order_line[0].id
                project = self.env["project.project"].with_context(ctx).create({
                    "name": f"{order.name} - {order.partner_id.name}",
                    "sale_line_id": order.order_line[0].id if order.order_line else False,
                    "user_id": order.user_id.id,
                    "partner_id": order.partner_id.id,
                })
                projects = project
            # Create tasks for each project using the service
            for project in projects:
                for product in products_with_templates:
                    templates = product.product_tmpl_id.task_template_ids
                    if templates:
                        # Use the task checkpoint service to create tasks with checkpoint configurations
                        created_tasks = self.env['task.checkpoint.service'].create_tasks_from_templates(project, templates) 