# Cabinet Directory Module

## 📋 Overview

The **Cabinet Directory** module provides a comprehensive document management system for organizing physical and digital documents in a hierarchical cabinet structure. It allows users to create cabinets, folders, and sub-folders to efficiently manage documents with proper tracking and handover capabilities.

## 🎯 Features

### 📁 Cabinet Management
- **Cabinet Directories**: Create and manage physical cabinet locations
- **Work Location Integration**: Link cabinets to specific work locations
- **Responsible Person Assignment**: Assign users to manage specific cabinets
- **Hierarchical Organization**: Cabinet → Folder → Sub Folder Files

### 📂 Folder Organization
- **Directory Folders**: Organize documents by category within cabinets
- **License Authority Tracking**: Link folders to specific licensing authorities
- **Responsible Person Assignment**: Assign users to manage specific folders
- **Category-based Organization**: Group related documents together

### 📄 Sub Folder Files Management
- **Document Tracking**: Track individual files with detailed information
- **CRM Integration**: Link files to CRM leads and opportunities
- **Partner Management**: Associate files with specific partners/contacts
- **State Management**: Track file status (ON FILE / HANDED OVER)
- **Attachment Support**: Attach multiple documents to each file
- **Activity Tracking**: Full mail thread and activity tracking

### 🔄 Workflow Features
- **Handover Process**: Transfer files between users with proper documentation
- **Meeting Scheduling**: Schedule meetings related to specific files
- **Email Integration**: Send emails directly from file records
- **Activity Logging**: Track all activities and changes

## 🏗️ Module Structure

```
cabinet_directory/
├── models/
│   ├── cabinet.py          # Cabinet Directory model
│   ├── folder.py           # Directory Folder model
│   └── sub_folder_files.py # Sub Folder Files model
├── views/
│   ├── cabinet.xml         # Cabinet views
│   ├── folder.xml          # Folder views
│   └── sub_folder_files.xml # Sub folder views
├── wizard/
│   ├── meeting.xml         # Meeting scheduling wizard
│   └── handover.xml        # Handover wizard
├── security/
│   └── ir.model.access.csv # Access rights
├── demo/
│   └── demo_data.xml       # Demo data
└── static/                 # Static assets
```

## 📊 Data Models

### Cabinet Directory (`cabinet.directory`)
- **name**: Cabinet name
- **work_location_id**: Associated work location
- **user_id**: Responsible person
- **directory_ids**: One2many relationship to folders

### Directory Folder (`directory.folder`)
- **name**: Folder name
- **user_id**: Responsible person
- **cabinet_id**: Parent cabinet
- **license_authority_id**: Associated license authority
- **sub_folders_ids**: One2many relationship to sub folders

### Sub Folder Files (`sub.folder.files`)
- **name**: File name
- **lead_id**: Associated CRM lead
- **partner_id**: Associated partner
- **folder_id**: Parent folder
- **user_id**: Responsible person
- **state**: File status (on_file/handed)
- **document_ids**: Many2many relationship to documents
- **attachment_ids**: Many2many relationship to attachments

## 🚀 Installation

### Prerequisites
- Odoo 18.0
- Required modules: `base`, `crm`, `documents`, `hr`

### Installation Steps

1. **Copy the module** to your Odoo addons path:
   ```bash
   cp -r cabinet_directory /path/to/odoo/addons/
   ```

2. **Update the addons list** in Odoo:
   - Go to Apps → Update Apps List

3. **Install the module**:
   - Search for "Cabinet Directory" in Apps
   - Click Install
   - Or use command line:
   ```bash
   python3 odoo-bin -d your_database --init=cabinet_directory --load-demo
   ```

## 📖 Usage Guide

### 1. Creating a Cabinet Directory

1. Navigate to **Cabinet Directory** → **Cabinet Directories**
2. Click **Create**
3. Fill in the required fields:
   - **Name**: Cabinet name (e.g., "Legal Documents Cabinet")
   - **Work Location**: Select the physical location
   - **Responsible Person**: Assign a user to manage this cabinet
4. Click **Save**

### 2. Creating Directory Folders

1. Open a **Cabinet Directory**
2. In the **Directory Folders** tab, click **Create**
3. Fill in the fields:
   - **Name**: Folder name (e.g., "Contracts and Agreements")
   - **Responsible Person**: Assign a user
   - **License Authority**: Select the relevant authority
4. Click **Save**

### 3. Managing Sub Folder Files

1. Open a **Directory Folder**
2. In the **Sub Folders** tab, click **Create**
3. Fill in the details:
   - **Name**: File name
   - **Pipeline**: Link to CRM lead (optional)
   - **Contact**: Link to partner (optional)
   - **Responsible Person**: Assign a user
   - **State**: Set initial state (ON FILE)
   - **Attachments**: Upload or link documents
4. Click **Save**

### 4. File Workflow

#### Handing Over Files
1. Open a **Sub Folder File**
2. Click **Handed Over** button
3. Fill in the handover wizard:
   - **New Responsible Person**: Select the recipient
   - **Handover Date**: Set the date
   - **Notes**: Add any relevant notes
4. Click **Confirm**

#### Scheduling Meetings
1. Open a **Sub Folder File**
2. Click **Schedule Meeting** button
3. Fill in the meeting details:
   - **Subject**: Meeting title
   - **Date & Time**: Set meeting time
   - **Attendees**: Add participants
4. Click **Save**

#### Sending Emails
1. Open a **Sub Folder File**
2. Click **Send Email** button
3. Compose and send the email

## 🎮 Demo Data

The module includes comprehensive demo data to help you understand its functionality:

### Demo Cabinets
- **Legal Documents Cabinet**: Main office location
- **Financial Documents Cabinet**: Main office location  
- **Client Files Cabinet**: Branch office location

### Demo Folders
- **Contracts and Agreements**: Legal documents
- **Licenses and Permits**: Regulatory documents
- **Financial Reports**: Financial documents
- **Client Contracts**: Client-related documents

### Demo Sub Folder Files
- **ACME Corporation Contract**: ON FILE state
- **Business License Application**: ON FILE state
- **Q4 Financial Report**: HANDED OVER state
- **Tech Solutions Agreement**: ON FILE state
- **Import License**: ON FILE state
- **Annual Tax Report**: HANDED OVER state

### Demo Dependencies
- **Work Locations**: Main Office, Branch Office
- **License Authorities**: Ministry of Commerce, Customs Authority, Municipality
- **CRM Leads**: 6 sample leads
- **Partners**: Demo partners from base module
- **Attachments**: 4 sample PDF documents

## 🔧 Configuration

### Access Rights
The module provides the following access rights:
- **Cabinet Directory**: Full access for users
- **Directory Folder**: Full access for users
- **Sub Folder Files**: Full access for users
- **Meeting Wizard**: Full access for users
- **Handover Wizard**: Full access for users

### Customization
You can customize the module by:
- Adding new fields to models
- Creating custom views
- Extending workflows
- Adding custom reports

## 🔗 Integration

### CRM Integration
- Link files to CRM leads and opportunities
- Track sales pipeline documents
- Schedule meetings with leads

### Document Management
- Integrate with Odoo Documents module
- Link to partner documents
- Manage attachments efficiently

### HR Integration
- Use HR work locations
- Assign responsible persons
- Track employee assignments

## 🐛 Troubleshooting

### Common Issues

1. **Demo data not loading**:
   - Ensure all dependencies are installed
   - Check that CRM module has demo data
   - Verify work locations exist

2. **Permission errors**:
   - Check user access rights
   - Verify group assignments
   - Review security rules

3. **Missing references**:
   - Ensure all referenced records exist
   - Check demo data dependencies
   - Verify external IDs

### Support
For issues or questions:
- Check the Odoo logs for error messages
- Verify module dependencies
- Test with clean database

## 📝 Changelog

### Version 18.0.1.0.0
- Initial release
- Cabinet directory management
- Folder organization
- Sub folder files tracking
- Handover workflow
- Meeting scheduling
- Email integration
- Demo data included

## 🤝 Contributing

To contribute to this module:
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

This module is licensed under LGPL-3.0.

---

**Author**: Beshoy Wageh  
**Version**: 18.0.1.0.0  
**Category**: Document Management 