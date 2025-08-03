# Migration Plan: Parallel x_ Views (Option 2)

## Goal
Introduce new x_ models and fields for required/deliverable documents in parallel with legacy models, allowing gradual migration, side-by-side testing, and risk mitigation.

---

## Steps

### 1. Inventory All Affected Views and Actions
- List all XML files, actions, and smart buttons referencing:
  - `project.document.required.line`
  - `project.document.type.line`
  - Legacy fields (e.g., `document_type_id`, `document_id`, etc.)

### 2. Duplicate Views for x_ Models
- For each affected view:
  - Create a new view (list/form) for the x_ model:
    - `project.required.document` (x_ fields)
    - `project.deliverable.document` (x_ fields)
  - Add these views to the UI in parallel with the legacy views (e.g., as new tabs or menu items).

### 3. Update/Extend Actions and Smart Buttons
- Add new actions, menu items, or smart buttons for the x_ models and fields, without removing the legacy ones.

### 4. Test in Parallel
- Use both legacy and x_ views in the UI.
- Compare behavior, data, and workflows.
- Gradually migrate data and user adoption to the new x_ models.

### 5. Switch Over
- Once confident, remove or hide the legacy views and actions.
- Make the x_ views and models primary.

### 6. Remove Legacy Code (Optional)
- After full migration and testing, remove or comment out all legacy models, views, and related code.

---

## Notes
- This approach is best for gradual, low-risk migration.
- Both legacy and new x_ models will coexist during the transition period.
- Allows for side-by-side testing and user training before final switchover.