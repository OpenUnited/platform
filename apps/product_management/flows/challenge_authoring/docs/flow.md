# Challenge and Bounty Posting Flow

## Overview
The Challenge creation process implements a modular flow pattern for challenge and bounty creation within a secure, role-based framework. The system uses Django's flow architecture with dedicated forms, services, and views, integrating with the central RoleService for access management.

## Directory Structure
The flow follows a modular structure with dedicated directories for each component:

### Core Files
- `__init__.py` - Flow configuration and documentation
- `forms.py` - Form definitions and validation
- `services.py` - Business logic, security, and data handling
- `views.py` - View handling and permission checks
- `urls.py` - URL routing

### Templates
Located in `templates/`:
- `main.html` - Main flow template
- Components in `templates/components/`:
  - Step templates (step_1.html through step_5.html)
  - Navigation (step_nav.html)
  - Modals and widgets (bounty_modal.html, skill_tree.html)

### Static Files
Located in `static/`:
- JavaScript modules in `js/`:
  - `main.js` - Core flow management
  - `bounty_modal.js` - Bounty configuration interface
  - `form_validation.js` - Client-side validation
  - `expertise_selector.js` - Expertise selection widget
- Stylesheets in `css/`:
  - `bounty_modal.css` - Modal-specific styles

## System Architecture

### 1. Flow Structure
Located in `apps/product_management/flows/challenge_authoring/`:
- `__init__.py` - Flow configuration and documentation
- `forms.py` - Form definitions and validation
- `services.py` - Business logic, security, and data handling
- `views.py` - View handling and permission checks
- `urls.py` - URL routing

### 2. Components
- **Forms**: Decoupled from models, working through service layer
- **Service**: Handles validation, security, and business rules
- **Views**: Product-aware views with permission checks
- **Security**: Integrated RoleService for access control
- **Templates**: Modular template structure

### 3. Data Flow
1. User accesses `/product-slug/challenge/create/`
2. RoleService validates user permissions
3. Challenge details are collected and validated
4. Bounties are added and configured
5. Service layer validates all data and permissions
6. Transaction creates challenge and bounties

### 4. Security Integration
- Centralized RoleService for permission management
- Multi-level permission validation
- Transaction-level security checks
- Role-based UI adaptations

### 5. API Endpoints
- `/<product_slug>/challenge/create/` - Main flow endpoint (requires manager role)
- `/skills/` - Get list of available skills (requires authentication)
- `/skills/<skill_id>/expertise/` - Get expertise options for a skill (requires authentication)

## Security and Access Management

### 1. Role-Based Access Control
#### Required Roles
- Product Manager or Admin role required for challenge creation
- Organization-level permissions respected
- Hierarchical permission structure

#### Permission Hierarchy
```python
# Example role checks
RoleService.is_product_manager(person, product)
RoleService.is_product_admin(person, product)
RoleService.is_organisation_manager(person, organisation)
```

#### RoleService Integration
```python
class ChallengeAuthoringService:
    def __init__(self, user, product_slug: str):
        self.role_service = RoleService()
        if not self._can_create_challenges():
            raise PermissionDenied
            
    def _can_create_challenges(self) -> bool:
        return self.role_service.is_product_manager(
            person=self.user.person,
            product=self.product
        )
```

### 2. Permission Validation
#### View-Level Checks
```python
class ChallengeAuthoringView(FormView):
    def dispatch(self, request, *args, **kwargs):
        if not RoleService.is_product_manager(
            person=request.user.person,
            product=self.product
        ):
            raise PermissionDenied
```

#### Service-Level Validation
- Pre-transaction permission checks
- Role verification before operations
- Organization-level permission validation

#### Transaction Security
- Atomic transactions with permission checks
- Rollback on permission failures
- Audit logging of security events

### 3. Error Handling
#### Permission Errors
- Clear user feedback for permission issues
- Appropriate HTTP status codes
- Secure error messages

#### Access Denied Flows
- Redirect to appropriate error pages
- Clear explanation of required permissions
- User guidance for access requests

#### Security Logging
- Authentication attempts
- Permission failures
- Critical operation logging

## Implementation Details

### 1. Service Layer
The `ChallengeAuthoringService` handles core business logic and security:

```python
class ChallengeAuthoringService:
    def __init__(self, user, product_slug: str):
        self.user = user
        self.product = self._get_product(product_slug)
        self.role_service = RoleService()
        
        if not self._can_create_challenges():
            raise PermissionDenied

    @transaction.atomic
    def create_challenge(self, challenge_data: Dict, bounties_data: List) -> Tuple[bool, Optional[Challenge], Optional[Dict]]:
        try:
            self.validate_challenge_data(challenge_data)
            self.validate_bounties_data(bounties_data)
            
            challenge = Challenge.objects.create(
                **challenge_data,
                product=self.product,
                created_by=self.user
            )
            
            self._create_bounties(challenge, bounties_data)
            return True, challenge, None
            
        except ValidationError as e:
            return False, None, e.message_dict
```

### 2. Forms
Forms handle data validation and cleaning:

```python
class ChallengeAuthoringForm(forms.Form):
    title = forms.CharField(max_length=200, min_length=10)
    description = forms.CharField(widget=forms.Textarea, max_length=5000, min_length=50)
    product_area = forms.ModelChoiceField(queryset=None, required=False)
    initiative = forms.ModelChoiceField(queryset=None, required=False)
    
    def __init__(self, *args, **kwargs):
        self.product_slug = kwargs.pop('product_slug', None)
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        self._init_product_fields()
```

### 3. Views
Views manage request handling and permission checks:

```python
class ChallengeAuthoringView(FormView):
    template_name = 'main.html'
    form_class = ChallengeAuthoringForm
    
    def dispatch(self, request, *args, **kwargs):
        if not hasattr(request.user, 'person'):
            raise PermissionDenied
            
        self.product = get_object_or_404(Product, slug=kwargs['product_slug'])
        
        if not RoleService.is_product_manager(
            person=request.user.person,
            product=self.product
        ):
            raise PermissionDenied
            
        return super().dispatch(request, *args, **kwargs)
```

## Validation and Business Rules

### 1. Challenge Validation
- Title length: 10-200 characters
- Description length: 50-5000 characters
- Required fields: title, description
- Optional fields: product_area, initiative
- User must have appropriate permissions

### 2. Bounty Validation
- Points range: 1-1000
- Maximum bounties per challenge: 10
- Required fields: title, points

## Development Guide

### 1. Adding New Features
When extending the challenge authoring flow:

```python
# 1. Add new permission check to RoleService if needed
@staticmethod
def has_custom_permission(person: Person, product: Product) -> bool:
    return RoleService.has_product_role(
        person=person,
        product=product,
        roles=['custom_role']
    )

# 2. Implement validation in service layer
def validate_new_feature(self, data: Dict) -> None:
    if not self.role_service.has_custom_permission(
        self.user.person, 
        self.product
    ):
        raise ValidationError("Permission denied")
```

### 2. Security Best Practices
1. **Permission Checks**
   - Always use RoleService for permissions
   - Implement checks at both view and service levels
   - Validate before any database operations
   - Use atomic transactions for multi-step operations

2. **Data Validation**
   - Validate all input data
   - Sanitize user inputs
   - Check file uploads for security
   - Validate relationships between entities

3. **Error Handling**
   - Use appropriate HTTP status codes
   - Provide clear error messages
   - Log security-related errors
   - Implement proper exception handling

### 3. Testing Strategy

#### Unit Tests
```python
class ChallengeAuthoringTests(TestCase):
    def setUp(self):
        self.user = UserFactory()
        self.product = ProductFactory()
        self.service = ChallengeAuthoringService(
            user=self.user,
            product_slug=self.product.slug
        )

    def test_permission_checks(self):
        # Test permission validation
        with self.assertRaises(PermissionDenied):
            ChallengeAuthoringService(
                user=self.unauthorized_user,
                product_slug=self.product.slug
            )

    def test_challenge_creation(self):
        # Test successful challenge creation
        success, challenge, errors = self.service.create_challenge(
            self.valid_challenge_data,
            self.valid_bounties_data
        )
        self.assertTrue(success)
        self.assertIsNone(errors)
```

#### Integration Tests
- Test complete flow from URL to database
- Verify permission checks
- Test transaction rollbacks
- Validate error handling

## Maintenance and Operations

### 1. Common Tasks

#### Adding New Role Types
1. Update RoleService with new role methods
2. Add role to model choices
3. Update permission checks
4. Update tests

#### Modifying Validation Rules
1. Update service layer validation
2. Update form validation
3. Update UI feedback
4. Update tests

### 2. Troubleshooting

#### Permission Issues
1. Check user has person object
2. Verify product/organization roles
3. Check RoleService logs
4. Verify transaction rollbacks

#### Common Errors
- Missing person object
- Invalid role assignments
- Transaction failures
- Validation errors

### 3. Performance Optimization

#### Database Queries
- Use select_related for foreign keys
- Use prefetch_related for reverse relations
- Cache permission checks where appropriate
- Optimize transaction handling

#### Security Overhead
- Cache role assignments
- Batch permission checks
- Optimize validation routines
- Use database constraints

### 4. Security Monitoring

#### Logging
```python
import logging
logger = logging.getLogger(__name__)

class ChallengeAuthoringService:
    def create_challenge(self, challenge_data, bounties_data):
        try:
            # Operation logic
            logger.info(
                "Challenge created",
                extra={
                    "user_id": self.user.id,
                    "product_id": self.product.id,
                    "challenge_data": challenge_data
                }
            )
        except Exception as e:
            logger.error(
                "Challenge creation failed",
                extra={
                    "user_id": self.user.id,
                    "error": str(e)
                }
            )
```

#### Monitoring Points
- Failed permission checks
- Transaction failures
- Invalid role assignments
- Suspicious activity patterns

#### Alerts
- Configure alerts for:
  - Multiple permission failures
  - Transaction rollbacks
  - Critical error patterns
  - Unusual activity volumes
