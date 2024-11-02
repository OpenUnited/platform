# URL and ID Standardization Guide

You are helping standardize URL patterns and HTML IDs in a Django project. Here are the key conventions and context:

## URL Patterns
1. All URL pattern names should use hyphens, not underscores
2. Exception: Namespace prefixes like `canopy:` can remain
3. Examples of correct patterns:
   - `product-detail`
   - `create-bounty`
   - `add-product-user`
   - `canopy:add-node`

## HTML IDs
1. Dynamic/Form-related IDs should keep underscores:
   - Form field IDs: `id_skills-0-expertise`
   - Generated content: `li_node_{{id}}`
   - Django form elements: `id_{{ form.field.name }}`
   - Dynamic components: `attachment-{{ index }}`

2. Static content IDs should use hyphens:
   - `form-container` (not `form_container`)
   - `user-table` (not `user_table`)
   - `product-content` (not `product_content`)
   - `ideas-and-bugs-content` (not `ideas_and_bugs_content`)

## File Structure
- Template location: `apps/product_management/templates/`
- URLs file: `apps/product_management/urls.py`
- Views location: `apps/product_management/views/`

## Verification Commands
```bash
# Check for underscore URL patterns
grep -r "url('.*_.*'" apps/product_management/templates/

# Check for underscore IDs (excluding form IDs)
grep -r "id=\"[^{]*_" apps/product_management/templates/

# Check URL pattern definitions
grep -r "name=" apps/product_management/urls.py
```

## Task
Please help standardize the following code according to these conventions. Keep in mind:
1. Don't change form-related IDs
2. Don't change dynamic template variables
3. Convert static IDs to use hyphens
4. Ensure all URL pattern names use hyphens

Would you like me to:
1. Show the specific changes needed?
2. Create a script to implement these changes?
3. Verify existing patterns against these conventions?
