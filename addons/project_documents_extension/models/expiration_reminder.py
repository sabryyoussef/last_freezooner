# -*- coding: utf-8 -*-

from odoo import models, fields, api
import datetime


class ProjectDocumentExpirationReminder(models.Model):
    _inherit = 'project.document.type.line'

    def check_for_expiration(self):
        """Check for expired documents and send reminders"""
        documents = self.search([
            ('expiration_reminder', '=', True), 
            ('expiration_reminder_sent', '=', False)
        ])
        today = datetime.datetime.now()
        thirty_days_from_today = today + datetime.timedelta(days=30)
        expired_documents = [
            document for document in documents 
            if document.expiration_date and document.expiration_date < thirty_days_from_today.date()
        ]
        
        for document in expired_documents:
            # Send email reminder
            self._send_expiration_reminder(document)
            document.write({'expiration_reminder_sent': True})

    def _send_expiration_reminder(self, document):
        """Send expiration reminder email"""
        # Create a simple email template for now
        # You can enhance this with proper mail templates later
        subject = f"Document Expiration Reminder: {document.document_type_id.name}"
        body = f"""
        <p>Hello,</p>
        <p>The following document is expiring soon:</p>
        <ul>
            <li><strong>Document:</strong> {document.document_type_id.name}</li>
            <li><strong>Expiry Date:</strong> {document.expiry_date}</li>
            <li><strong>Project:</strong> {document.project_id.name if document.project_id else 'N/A'}</li>
            <li><strong>Task:</strong> {document.task_id.name if document.task_id else 'N/A'}</li>
        </ul>
        <p>Please take necessary action to renew or update this document.</p>
        """
        
        # Send email to project manager or task assignee
        recipients = []
        if document.project_id.user_id:
            recipients.append(document.project_id.user_id.email)
        if document.task_id.user_id:
            recipients.append(document.task_id.user_id.email)
        
        if recipients:
            self.env['mail.mail'].create({
                'subject': subject,
                'body_html': body,
                'email_to': ','.join(set(recipients)),
                'auto_delete': True,
            }).send()


class ProjectDocumentRequiredExpirationReminder(models.Model):
    _inherit = 'project.document.required.line'

    def check_for_expiration(self):
        """Check for expired documents and send reminders"""
        documents = self.search([
            ('expiration_reminder', '=', True), 
            ('expiration_reminder_sent', '=', False)
        ])
        today = datetime.datetime.now()
        thirty_days_from_today = today + datetime.timedelta(days=30)
        expired_documents = [
            document for document in documents 
            if document.expiration_date and document.expiration_date < thirty_days_from_today.date()
        ]
        
        for document in expired_documents:
            # Send email reminder
            self._send_expiration_reminder(document)
            document.write({'expiration_reminder_sent': True})

    def _send_expiration_reminder(self, document):
        """Send expiration reminder email"""
        # Create a simple email template for now
        # You can enhance this with proper mail templates later
        subject = f"Required Document Expiration Reminder: {document.document_type_id.name}"
        body = f"""
        <p>Hello,</p>
        <p>The following required document is expiring soon:</p>
        <ul>
            <li><strong>Document:</strong> {document.document_type_id.name}</li>
            <li><strong>Expiry Date:</strong> {document.expiry_date}</li>
            <li><strong>Project:</strong> {document.project_id.name if document.project_id else 'N/A'}</li>
            <li><strong>Task:</strong> {document.task_id.name if document.task_id else 'N/A'}</li>
        </ul>
        <p>Please take necessary action to renew or update this document.</p>
        """
        
        # Send email to project manager or task assignee
        recipients = []
        if document.project_id.user_id:
            recipients.append(document.project_id.user_id.email)
        if document.task_id.user_id:
            recipients.append(document.task_id.user_id.email)
        
        if recipients:
            self.env['mail.mail'].create({
                'subject': subject,
                'body_html': body,
                'email_to': ','.join(set(recipients)),
                'auto_delete': True,
            }).send() 