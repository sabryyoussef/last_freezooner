# Project Documents Extension: Workflow & Migration Mapping

This document maps all document-related features in the frontend (UI) to their backend models, fields, and services. It indicates whether each feature uses legacy or new x_ models, and provides notes for migration to a modern, x_ only workflow.

---

## UI to Backend Mapping Table

| UI Location (Frontend)                | Backend Model/Field/Service                | Legacy or x_ | Notes/Action Needed                |
|---------------------------------------|--------------------------------------------|--------------|------------------------------------|
| Project > Required Documents Tab      | `project.document.required.line` via `document_required_type_ids` | Legacy       | Will migrate to `x_required_document_ids` |
| Project > Deliverable Documents Tab   | `project.document.type.line` via `document_type_ids` | Legacy       | Will migrate to `x_deliverable_document_ids` |
| Project > x_Required Documents Tab    | `project.required.document` via `x_required_document_ids` | x_           | New model, keep and enhance        |
| Project > x_Deliverable Documents Tab | `project.deliverable.document` via `x_deliverable_document_ids` | x_           | New model, keep and enhance        |
| Sale Order > Product Line             | `product.template.document_required_type_ids`/`document_type_ids` | Legacy       | Will migrate to x_ fields          |
| Sale Order > Product Line             | `product.template.x_required_document_ids`/`x_deliverable_document_ids` | x_           | New model, keep and enhance        |
| Project Chatter (Document Logs)       | `project.document.service`                 | Both         | Update to use x_ only              |
| Task > Required/Deliverable Documents | `project.task.document_required_type_ids`/`document_type_ids` | Legacy       | Will migrate to x_ fields          |
| Task > x_Required/x_Deliverable Docs  | `project.task.x_required_document_ids`/`x_deliverable_document_ids` | x_           | New model, keep and enhance        |

---

## Migration Workflow

1. **Document all UI features and their backend references (see table above).**
2. **For each feature:**
    - Build a parallel backend logic and view for x_ models (if not already present).
    - Update the UI to support both legacy and x_ models during transition.
    - Test the new x_ workflow in parallel with the legacy one.
3. **Once all features are supported by x_ models:**
    - Remove legacy model usage from backend logic and views.
    - Clean up database and codebase (remove legacy fields/models/views).
    - Update documentation and user training to reference only the new x_ workflow.

---

## Example Migration Steps

- [ ] Project > Required Documents Tab: Switch from `document_required_type_ids` to `x_required_document_ids`.
- [ ] Project > Deliverable Documents Tab: Switch from `document_type_ids` to `x_deliverable_document_ids`.
- [ ] Sale Order > Product Line: Use only x_ fields for document configuration.
- [ ] Project Chatter: Update logging and reporting to use x_ models.
- [ ] Task Views: Migrate to x_ document fields for all document-related features.
- [ ] Remove all legacy model references and fields from codebase.

---

## Notes
- This file should be updated as you migrate each feature.
- Use this as a checklist and reference for a clean, modern document workflow in your Odoo project.