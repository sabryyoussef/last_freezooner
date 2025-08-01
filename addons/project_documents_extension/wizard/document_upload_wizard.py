from odoo import _, api, fields, models
from odoo.exceptions import ValidationError

class DocumentUploadWizard(models.TransientModel):
    _name = 'document.upload.wizard'
    _description = 'Document Upload Wizard'

    project_id = fields.Many2one('project.project', string='Project', required=True)
    user_id = fields.Many2one('res.users', string='User', required=True)
    name = fields.Char('Document Name', required=True)
    document_type = fields.Selection([
        ('required', 'Required Document'),
        ('deliverable', 'Deliverable Document')
    ], string='Document Type', required=True)
    comment = fields.Text('Comment')

    def action_upload(self):
        for rec in self:
            project = rec.project_id
            body = _(
                "<b>Upload Document.</b><br/>"
                "<b>Comment:</b> %(comment)s<br/>"
                "<b>For:</b> <a href='#' data-oe-model='project.project' data-oe-id='%(partner_id)d'>@%(user_name)s</a><br/><br/>"
            ) % {
                "comment": rec.comment or "Upload Document",
                "partner_id": (rec.user_id.partner_id.id if rec.user_id.partner_id else 0),
                "user_name": (rec.user_id.partner_id.name if rec.user_id.partner_id else "Unknown User"),
            }
            # Log a note in the chatter
            message = project.message_post(
                body=body,
                message_type="comment",
                subtype_xmlid="mail.mt_note",
                partner_ids=([rec.user_id.partner_id.id] if rec.user_id.partner_id else []),
            )
            # Create a notification manually for only the mentioned user if it doesn't already exist
            if message and rec.user_id.partner_id:
                existing_notification = self.env["mail.notification"].search(
                    [
                        ("mail_message_id", "=", message.id),
                        ("res_partner_id", "=", rec.user_id.partner_id.id),
                    ],
                    limit=1,
                )
                if not existing_notification:
                    self.env["mail.notification"].create(
                        {
                            "mail_message_id": message.id,
                            "res_partner_id": rec.user_id.partner_id.id,  # Notify only this partner
                            "notification_type": "inbox",  # Store in inbox, no email
                            "is_read": False,  # Mark as unread
                        }
                    )
            return {
                "name": "Document",
                "type": "ir.actions.act_window",
                "res_model": "documents.document",
                "view_mode": "form",
                "context": {
                    "default_project_id": rec.project_id.id,
                    "default_folder_id": rec.project_id.documents_folder_id.id if rec.project_id.documents_folder_id else False,
                    "default_user_id": rec.user_id.id,
                    "default_name": rec.name,
                },
                "target": "new",
            } 