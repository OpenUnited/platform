# Notification System Design

## Core Concepts

### Event-Driven Architecture
- Events are published when significant actions occur
- Events are processed via Django Q (configurable sync/async)
- Events are logged in EventLog model with retention period
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

### 5. Task Processors
- Asynchronous notification creation
- Template rendering
- Error handling with fallback notifications
- Preference-based notification routing

### 6. EventTypes Registry
- Centralized registry of all application events
- Provides validation and display names
- Used by EventLog and templates
- Supports test events and product events

## Example Flow: Product Creation Notification

### Step 1: Event Publication
When a product is created, the ProductManagementService publishes an event with the product details and ownership information.

### Step 2: Event Processing
The system uses a multi-layer approach:

1. **Event Bus**:
   - Validates events against EventTypes registry
   - Logs events in EventLog model
   - Handles sync/async execution configuration
   - Manages task queuing and execution

2. **Event Handlers** (`events.py`):
   - Handle specific event types (e.g., handle_product_created)
   - Identify relevant stakeholders
   - Create NotifiableEvent records
   - Queue notification processing tasks

3. **Task Processors** (`tasks.py`):
   - Process NotifiableEvent records
   - Check user notification preferences
   - Handle template rendering
   - Create AppNotification and EmailNotification records
   - Include error handling and fallback notifications

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
    
    # Publish event
    event_bus = get_event_bus()
    event_bus.publish('product.created', {
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

    
    AppNotification.objects.create(
        event=event,
        title="Notification",
        message=message
    )
    
    return event
def handle_product_created(event_data):
    """Handle product created event by creating NotifiableEvents for relevant stakeholders"""
    try:
        product_id = event_data.get('product_id')
        if not product_id:
            logger.error("No product_id in event payload")
            return False
            
        try:
            product = Product.objects.get(id=product_id)
        except Product.DoesNotExist:
            logger.error(f"Product {product_id} not found")
            return False

        # Get all stakeholders to notify
        people_to_notify = set()
        
        if product.organisation:
            people_to_notify.update(RoleService.get_organisation_managers(product.organisation))
            people_to_notify.update(RoleService.get_product_managers(product))
        elif product.person:
            people_to_notify.add(product.person)
            
        if not people_to_notify:
            person_id = event_data.get('person_id')
            if person_id:
                try:
                    person = Person.objects.get(id=person_id)
                    people_to_notify.add(person)
                except Person.DoesNotExist:
                    logger.error(f"Person {person_id} not found")
        
        # Create events for each person
        events = []
        for person in people_to_notify:
            event = NotifiableEvent.objects.create(
                event_type=EventTypes.PRODUCT_CREATED,
                person=person,
                params=event_data
            )
            events.append(event)
            
            EventBus().enqueue_task(
                'apps.engagement.tasks.process_notification',
                {'event_id': event.id},
                EventTypes.PRODUCT_CREATED
            )
        return len(events) > 0
        
    except Exception as e:
        logger.error(f"Error in handle_product_created: {e}", exc_info=True)
        raise
def handle_product_updated(event_data):
    """Handle product updated event"""
    logger.info(f"Handling product updated event: {event_data}")
    
    event = NotifiableEvent.objects.create(
        event_type=EventTypes.PRODUCT_UPDATED,
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
   - Event is published with product details

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
- **Event Processing Tests**: Verify event handling and task execution
- **Event Bus Tests**: Test publication and subscription
- **Multiple Listener Tests**: Verify parallel execution
- **Transaction Tests**: Ensure proper transaction handling
- **Error Cases**: System resilience testing

### 2. Test Infrastructure

1. **Base Test Setup**
```python
@pytest.fixture(autouse=True)
def enable_db_access_for_all_tests(db):
    pass

@pytest.fixture(autouse=True)
def clear_cache():
    cache.clear()
    yield
    cache.clear()
```

2. **Async Test Environment**
```python
@pytest.fixture(autouse=True)
def setup_async_environment():
    broker = get_broker()
    broker.purge_queue()
    
    ready_event = Event()
    cluster = Cluster(broker)
    cluster.start()
    ready_event.wait(timeout=1)
    
    yield
    
    cluster.stop()
    broker.purge_queue()
    cache.clear()
```

### 3. Testing Patterns

1. **Synchronous Flow Testing**
   - Direct handler calls
   - Immediate assertion checking
   - Used for preference and template testing

2. **Asynchronous Flow Testing**
   - Django Q cluster setup
   - Exponential backoff waiting
   - Race condition handling

3. **Test Helpers**
```python
@pytest.fixture
def wait_for_notifications():
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

### 4. Best Practices

1. **Test Isolation**
   - Use transaction rollback
   - Clear queues between tests
   - Reset cache state

2. **Async Testing**
   - Configure Django Q for testing
   - Handle timeouts appropriately
   - Clean up broker queues

3. **Preference Testing**
   - Test all notification types
   - Verify correct routing
   - Check template rendering

4. **Error Handling**
   - Test missing templates
   - Verify fallback notifications
   - Check error logging

### Event Logging
Events are logged in the EventLog model with:
- Event type validation against central registry
- JSON payload storage
- Processing status tracking
- Configurable retention period
- Automatic cleanup via delete_at field
