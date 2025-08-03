# Migration Plan: Replace All References to x_ Models (Option 1)

## Goal
Migrate all views, actions, and logic from the legacy required/deliverable document models to the new x_ models and fields, fully deprecating the old models.

---

## Steps

### 1. Inventory All Affected Views and Actions
- List all XML files, actions, and smart buttons referencing:
  - `project.document.required.line`
  - `project.document.type.line`
  - Legacy fields (e.g., `document_type_id`, `document_id`, etc.)

### 2. Update Views
- For each affected view:
  - Change the `model` attribute to the new x_ model:
    - `project.document.required.line` → `project.required.document`
    - `project.document.type.line` → `project.deliverable.document`
  - Update all field names to their x_ equivalents (e.g., `x_document_type_id`).

### 3. Update Actions and Smart Buttons
- Update any actions, menu items, or smart buttons to use the new models and fields.

### 4. Update Python Logic
- Refactor any server-side logic, wizards, or computed fields to use the new x_ models and fields.

### 5. Test
- Test all affected forms, lists, and workflows to ensure the new models and fields work as expected.

### 6. Remove Legacy Code
- Once migration is complete and tested, remove or comment out all legacy models, views, and related code.

---

## Notes
- This approach is best for a clean, immediate migration.
- All new and existing data should be migrated to the new x_ models if needed.
- Legacy data and code will be fully deprecated after migration.