# Portal Architecture Principles

## Overview
The Portal app follows a set of pragmatic architectural principles focused on simplicity, maintainability, and developer experience. These principles guide how we structure code, handle business logic, and build user interfaces.

## Core Principles

### 1. Simplicity & Comprehensibility
- Code should be easily understood by both LLMs and humans
- Favor explicit over implicit patterns
- Use descriptive naming that reveals intent
- Maintain flat hierarchies where possible
- Document key architectural decisions

### 2. Service Layer Architecture
- Business logic lives in `services.py`
- Views orchestrate services but don't contain business logic
- Services can use other app services (e.g., RoleService from security)
- Keep services focused and composable

### 3. Template Structure
- Use Django templates, following Django conventions
- Organize templates by feature domain
- Keep components reusable and well-structured

For example, when building a user management feature:

    templates/portal/users/
    ├── list.html          # Shows all users
    ├── detail.html        # Shows single user profile
    ├── edit.html          # Edit user form
    └── components/        # User-specific components
        ├── user_card.html # Reusable user profile card
        └── filters.html   # User list filtering controls

This organization keeps all user-related templates together, making it easy to:
- Find and modify related templates
- Maintain consistent styling and behavior
- Reuse common components within the feature
- Add new user-related templates in a logical location

Bad practice would be mixing features together like:

    templates/portal/
    ├── list_users.html
    ├── list_products.html
    ├── user_detail.html
    ├── product_detail.html

### 4. Frontend Architecture
- Use TailwindCSS and TailwindUI for styling
- Employ modern, vanilla JavaScript (no jQuery or TypeScript)
- Prefer server-side rendering where possible
- Use JavaScript for progressive enhancement only

### 5. View Layer
- Keep views thin and focused
- Handle routing, request/response, and template rendering
- Delegate business logic to services
- Focus on orchestration rather than implementation

### 6. Directory Structure
The portal app follows a standard Django app structure with clear separation of concerns:

    apps/portal/
    ├── templates/          # Django templates
    │   └── portal/        # Namespace for portal templates
    │       ├── base.html  # Base template
    │       ├── components/# Reusable UI components
    │       ├── products/  # Product-related templates
    │       ├── bounties/  # Bounty-related templates
    │       ├── challenges/# Challenge-related templates
    │       └── work/      # Work-related templates
    ├── static/            # Static assets
    │   ├── js/           # JavaScript modules
    │   └── css/          # Custom CSS (if needed)
    ├── views.py          # URL routing and request handling
    ├── services.py       # Business logic
    ├── forms.py          # Form definitions
    └── urls.py           # URL configuration

#### Template Directory Structure
The templates follow a feature-based organization:

    templates/portal/
    ├── base.html                         # Base template with common structure
    ├── components/                       # Reusable components
    │   ├── attachments.html             # File attachment handling
    │   └── side_menu.html              # Navigation menu
    ├── products/                        # Product feature templates
    │   ├── detail.html                 # Product details
    │   ├── settings.html               # Product settings
    │   └── users/                      # Product user management
    │       ├── add.html                # Add user
    │       ├── manage.html             # User list/management
    │       └── update.html             # Edit user
    ├── bounties/                        # Bounty feature templates
    │   ├── claims.html                 # Bounty claims
    │   ├── manage.html                 # Bounty management
    │   ├── my_bounties.html           # User's bounties
    │   └── components/                 # Bounty-specific components
    │       └── table.html             # Bounty listing table
    ├── challenges/                      # Challenge feature templates
    │   ├── manage.html                 # Challenge management
    │   └── components/                 # Challenge-specific components
    │       └── table.html             # Challenge listing table
    └── work/                           # Work review templates
        ├── review.html                 # Work review interface
        └── components/                 # Work-specific components
            └── table.html             # Work review table

## Implementation Guidelines

### Code Organization
- Group related functionality together
- Keep files focused and single-purpose
- Use clear, consistent naming
- Document complex logic

### Service Layer
- Services handle business logic
- Views orchestrate services
- Keep services focused and testable
- Document service interfaces

### Templates
- Follow consistent structure
- Use components for reusability
- Keep logic in services
- Maintain clear hierarchy

### Frontend
- Progressive enhancement
- Server-side first
- Simple, focused JavaScript
- Consistent UI patterns

## Maintenance
- Regularly review and update principles
- Document significant deviations
- Keep dependencies current
- Monitor code quality
- Regular refactoring when needed
