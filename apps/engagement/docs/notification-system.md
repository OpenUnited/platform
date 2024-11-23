# Notification System Design

## Core Concepts

### Event-Driven Architecture
- Events are emitted when significant actions occur
- Events are processed asynchronously via Django Q
- Handlers create notifications based on event type and user preferences

### Notification Preferences
- Users can choose how they want to be notified (Apps, Email, Both, None)
- Preferences are stored per person and per event type
- Notifications are only created in the channels the user has enabled

### Notification Types
- **App Notifications**: Displayed in the web interface
- **Email Notifications**: Sent via email
- Both types use templates for consistent formatting

### Data Lifecycle
- Transient records (events, notifications) have `delete_at` fields
- Automatic cleanup of old records
- Templates and preferences are permanent

## System Components

### 1. Event Bus (Django Q)
The event bus handles asynchronous processing and decouples event producers from consumers.

### 2. NotifiableEvent
- Records that something notification-worthy happened
- Links event to specific person
- Stores event parameters
- Used by event handlers to create notifications

### 3. Notification Templates
- `AppNotificationTemplate`
- `EmailNotificationTemplate`
- Define how notifications are formatted
- Include parameter validation

### 4. Notification Records
- `AppNotification` (with read/unread status)
- `EmailNotification` (with sent status)
- Track actual notifications sent

## Example Flow: Product Creation Notification

### Step 1: Event Emission
When a product is created, the ProductManagementService emits an event with the product details and ownership information.

### Step 2: Event Processing
The Django Q worker picks up the event and routes it to the appropriate handler. The handler:
1. Validates the event payload and retrieves the product
2. Creates NotifiableEvent records for:
   - The product creator
   - Organization managers/owners (if org-owned product)
3. Includes error handling and logging

### Step 3: Notification Creation
The system:
1. Creates a NotifiableEvent record
2. Checks the recipient's notification preferences
3. Creates appropriate notifications based on those preferences
4. Handles errors gracefully:
   - Missing notification preferences
   - Missing notification templates
   - Template rendering errors

### Step 4: Notification Delivery
- App notifications appear in the web interface
- Email notifications are sent via email
- Users can mark app notifications as read
- Notifications are automatically cleaned up after their expiry date

## Key Benefits

### 1. Flexibility
- Easy to add new event types
- Easy to add new notification channels
- User-controlled preferences

### 2. Scalability
- Async processing via Django Q
- Efficient database queries
- Automatic cleanup

### 3. Maintainability
- Clear separation of concerns
- Template-based formatting
- Centralized notification logic

### 4. Reliability
- Event processing retries
- Database constraints
- Error logging

## Models

### NotifiableEvent
Represents an event that can trigger notifications:
- Links to specific person
- Contains event type and parameters
- Has deletion date for cleanup

### NotificationPreference
Stores user preferences for different notification types:
- One record per person
- Controls notification channels per event type (currently supports product notifications)

### AppNotification & EmailNotification
Track actual notifications:
- Link back to NotifiableEvent
- Include read/sent status
- Have deletion dates for cleanup

### Templates
Define how notifications look:
- Separate templates for app and email notifications
- Parameter validation
- Reusable across notifications of same type

## Examples

### 1. Emitting Events

````python`
# apps/capabilities/product_management/services.py

def create_product(form_data: dict, person: Person, organisation: Organisation = None) -> Product:
    # Create the product
    product = Product.objects.create(**product_data)
    
    # Emit event
    event_bus = get_event_bus()
    event_bus.emit_event('product.created', {
        'organisation_id': product.organisation_id if product.organisation else None,
        'person_id': product.person_id if product.person else None,
        'name': product.name,
        'url': product.get_absolute_url(),
        'product_id': product.id
    })
`````

### 2. Handling Events

````python`
# apps/engagement/events.py

def handle_product_created(payload: dict) -> None:
    """Handle product.created event"""
    logger.info(f"Processing product created event: {payload}")
    try:
        product_id = payload.get('product_id')
        if not product_id:
            logger.error("No product_id in payload")
            return
            
        product = Product.objects.get(id=product_id)
        
        params = {
            'name': payload.get('name', product.name),
            'url': payload.get('url', f'/products/{product.id}/summary/')
        }
        
        # Always notify the creator
        person_id = payload.get('person_id')
        if person_id:
            creator = Person.objects.get(id=person_id)
            event = NotifiableEvent.objects.create(
                event_type=NotifiableEvent.EventType.PRODUCT_CREATED,
                person=creator,
                params=params
            )
            _create_notifications_for_event(event)
        
        # If org-owned, also notify org admins
        if product.is_owned_by_organisation():
            admin_assignments = OrganisationPersonRoleAssignment.objects.filter(
                organisation=product.organisation,
                role__in=[
                    OrganisationPersonRoleAssignment.OrganisationRoles.OWNER,
                    OrganisationPersonRoleAssignment.OrganisationRoles.MANAGER
                ]
            ).exclude(person_id=person_id)  # Don't double-notify the creator
            
            for assignment in admin_assignments:
                event = NotifiableEvent.objects.create(
                    event_type=NotifiableEvent.EventType.PRODUCT_CREATED,
                    person=assignment.person,
                    params=params
                )
                _create_notifications_for_event(event)
`````

### 3. Creating Notifications

```python
def _create_notifications_for_event(event: NotifiableEvent) -> None:
    """Create notifications based on user preferences"""
    try:
        prefs = NotificationPreference.objects.get(person=event.person)
        if prefs.product_notifications in [NotificationPreference.Type.APPS, NotificationPreference.Type.BOTH]:
            template = AppNotificationTemplate.objects.get(event_type=event.event_type)
            AppNotification.objects.create(
                event=event,
                title=template.title_template.format(**event.params),
                message=template.message_template.format(**event.params)
            )
    except NotificationPreference.DoesNotExist:
        logger.warning(f"No notification preferences found for person {event.person.id}")
    except AppNotificationTemplate.DoesNotExist:
        logger.error(f"No app notification template found for event type {event.event_type}")
    except Exception as e:
        logger.error(f"Error creating notifications for event: {str(e)}")

### 4. Retrieving Notifications

````python`
# apps/engagement/services.py

class NotificationService:
    def get_unread_notifications(self, person: Person) -> QuerySet[AppNotification]:
        """Get all unread app notifications for a person"""
        return AppNotification.objects.filter(
            event__person=person,
            is_read=False
        ).select_related('event').order_by('-created_at')

    def mark_notification_as_read(self, notification_id: int, person: Person) -> bool:
        """Mark a specific notification as read"""
        try:
            notification = AppNotification.objects.get(
                id=notification_id,
                event__person=person
            )
            notification.mark_as_read()
            return True
        except AppNotification.DoesNotExist:
            return False
`````

### 5. Notification Templates

````python`
# apps/engagement/models.py

class AppNotificationTemplate(models.Model):
    """Templates for in-app notifications"""
    event_type = models.CharField(
        max_length=50, 
        choices=NotifiableEvent.EventType.choices, 
        primary_key=True
    )
    title_template = models.CharField(max_length=400)
    message_template = models.CharField(max_length=4000)
    permitted_params = models.CharField(max_length=500)

    def clean(self):
        _template_is_valid(self.title_template, self.permitted_params)
        _template_is_valid(self.message_template, self.permitted_params)
`````

### Detailed Product Creation Flow

1. **Product Creation**
   - Product is created via ProductManagementService
   - Creator is assigned as admin
   - Event is emitted with product details

2. **Event Processing**
   - Event is picked up by handler
   - Product is retrieved using product_id
   - Two notification paths:
     a. Creator notification
     b. Organization admin notification (if org-owned)

3. **Notification Creation**
   - Checks user preferences
   - Creates notifications based on template
   - Handles both app and email notifications
   - Includes error handling and logging

4. **Template Validation**
   - Templates are validated for permitted parameters
   - Invalid templates trigger appropriate error responses
   - Validation occurs at template creation/update

5. **Cleanup**
   - Notifications are automatically marked for deletion after 72 hours
   - Cleanup process removes expired notifications

## Email Notifications

### Implementation
Email notifications are handled similarly to app notifications but with additional considerations:

1. **Templates**
```python
class EmailNotificationTemplate(models.Model):
    event_type = models.CharField(max_length=50, choices=NotifiableEvent.EventType.choices)
    title = models.CharField(max_length=400)
    template = models.CharField(max_length=4000)
    permitted_params = models.CharField(max_length=500)
```

2. **Delivery**
- Email notifications are created in the database first
- Actual email sending is handled asynchronously
- Includes sent status tracking and error handling

3. **Lifecycle**
- Emails have a 72-hour retention period (delete_at field)
- Sent status is tracked for monitoring
- Failed deliveries are logged for investigation

## Testing Strategy

### 1. Test Categories
- **Basic Flow Tests**: Verify core notification creation and delivery
- **Async Behavior**: Test event processing and notification generation
- **Error Handling**: Validate system resilience
- **Performance**: Check system behavior under load
- **Edge Cases**: Test unusual scenarios
- **Maintenance**: Verify cleanup and housekeeping

### 2. Test Infrastructure
```python
# Global fixtures (conftest.py)
@pytest.fixture(autouse=True)
def enable_db_access_for_all_tests(db):
    """Enable database access for all tests"""
    pass

@pytest.fixture(autouse=True)
def use_transaction_db(transactional_db):
    """Make all tests transactional"""
    pass

@pytest.fixture(autouse=True)
def clear_cache():
    """Clear cache before/after tests"""
    cache.clear()
    yield
    cache.clear()
```

### 3. Key Test Scenarios
1. **Event Emission**
   - Verify correct event payload
   - Check async processing
   - Test concurrent events

2. **Notification Creation**
   - Test preference-based creation
   - Validate template rendering
   - Check error handling

3. **Email Specific**
   - Test email template rendering
   - Verify email queuing
   - Check delivery status tracking

4. **Performance Testing**
   - Test under high load
   - Check query optimization
   - Verify async processing scales

5. **Cleanup and Maintenance**
   - Test automatic deletion
   - Verify retention periods
   - Check cleanup efficiency

### 4. Test Helpers
```python
@pytest.fixture
def wait_for_notifications():
    """Wait for notifications with exponential backoff"""
    def _wait(filter_kwargs, expected_count=1, timeout=10):
        start_time = time.time()
        sleep_time = 0.1
        
        while time.time() - start_time < timeout:
            count = NotifiableEvent.objects.filter(**filter_kwargs).count()
            if count == expected_count:
                return True
            time.sleep(min(sleep_time, 0.5))
            sleep_time *= 1.5
        
        raise TimeoutError(f"Timed out waiting for {expected_count} notifications")
    return _wait
```

### 5. Best Practices
1. **Test Isolation**
   - Each test runs in its own transaction
   - Automatic cleanup of test data
   - Cache clearing between tests

2. **Async Testing**
   - Use django_q_cluster fixture
   - Handle race conditions
   - Proper timeout handling

3. **Error Scenarios**
   - Test template errors
   - Handle missing preferences
   - Validate error logging

4. **Performance Monitoring**
   - Track query counts
   - Monitor processing time
   - Check memory usage

5. **Maintenance Testing**
   - Verify cleanup jobs
   - Test retention policies
   - Check index usage
