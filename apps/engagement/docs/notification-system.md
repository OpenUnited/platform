# Notification System Design

## Core Concepts

### Event-Driven Architecture
- Events are published when significant actions occur
- Events are processed via Django Q (configurable sync/async)
- Events are logged in EventLog model with retention period
- Handlers create notifications based on event type and user preferences
- Events are processed synchronously in test environments

### Notification Preferences
- Users can choose notification delivery method:
  - Apps (web interface only)
  - Email only
  - Both channels
  - None (opt-out)
- Preferences are stored per person and per event type
- Notifications are only created in enabled channels

### Notification Types
- **App Notifications**: Displayed in the web interface
- **Email Notifications**: Sent via email
- Both types use templates for consistent formatting
- Templates include parameter validation

### Data Lifecycle
- Transient records (events, notifications) have `delete_at` fields
- Automatic cleanup of old records (72-hour retention)
- Templates and preferences are permanent
- Failed deliveries are logged for investigation

## System Components

### 1. Event Bus
```python
class EventBus:
    - Singleton pattern implementation
    - Supports both sync and async execution
    - Maintains registry of event listeners
    - Logs events in EventLog model
    - Handles execution errors gracefully
```

### 2. NotifiableEvent
- Records notification-worthy events
- Links events to specific persons
- Stores event parameters
- Used by event handlers to create notifications

### 3. Notification Templates
```python
class AppNotificationTemplate:
    - event_type: CharField (matches EventTypes registry)
    - title_template: CharField
    - template: CharField
    - permitted_params: CharField

class EmailNotificationTemplate:
    - event_type: CharField
    - title: CharField
    - template: CharField
    - permitted_params: CharField
```

### 4. Notification Records
```python
class AppNotification:
    - event: ForeignKey(NotifiableEvent)
    - title: CharField
    - message: CharField
    - is_read: BooleanField
    - delete_at: DateTimeField

class EmailNotification:
    - event: ForeignKey(NotifiableEvent)
    - title: CharField
    - body: CharField
    - sent: BooleanField
    - delete_at: DateTimeField
```

### 5. Task Processors
- Asynchronous notification creation
- Template rendering
- Error handling with fallback notifications
- Preference-based notification routing
- Transaction management

### 6. EventTypes Registry
- Centralized registry of all application events
- Provides validation and display names
- Used by EventLog and templates
- Supports test events and product events

## Example Flow: Product Creation Notification

### Step 1: Event Publication
```python
def create_product(form_data: dict, person: Person, organisation: Organisation = None) -> Product:
    product = Product.objects.create(**product_data)
    
    event_bus = get_event_bus()
    event_bus.publish('product.created', {
        'organisation_id': product.organisation_id,
        'person_id': product.person_id,
        'name': product.name,
        'url': product.get_absolute_url(),
        'product_id': product.id
    })
```

### Step 2: Event Processing
The system uses a multi-layer approach:

1. **Event Bus**:
   - Validates events against EventTypes registry
   - Logs events in EventLog model
   - Handles sync/async execution configuration
   - Manages task queuing and execution

2. **Event Handlers**:
```python
def handle_product_created(event_data):
    # Get all stakeholders to notify
    people_to_notify = set()
    
    if product.organisation:
        people_to_notify.update(RoleService.get_organisation_managers(product.organisation))
        people_to_notify.update(RoleService.get_product_managers(product))
    elif product.person:
        people_to_notify.add(product.person)
        
    # Create events and queue notifications
    for person in people_to_notify:
        event = NotifiableEvent.objects.create(
            event_type=EventTypes.PRODUCT_CREATED,
            person=person,
            params=event_data
        )
        
        EventBus().enqueue_task(
            'process_notification',
            {'event_id': event.id},
            EventTypes.PRODUCT_CREATED
        )
```

### Step 3: Notification Creation
The system:
1. Retrieves user notification preferences
2. Loads appropriate templates
3. Creates notifications based on preferences:
```python
def _create_notifications_for_event(event: NotifiableEvent) -> None:
    prefs = NotificationPreference.objects.get(person=event.person)
    
    if prefs.product_notifications in [NotificationPreference.Type.APPS, NotificationPreference.Type.BOTH]:
        template = AppNotificationTemplate.objects.get(event_type=event.event_type)
        AppNotification.objects.create(
            event=event,
            title=template.title_template.format(**event.params),
            message=template.message_template.format(**event.params)
        )
```

### Step 4: Notification Delivery
- App notifications appear immediately in web interface
- Email notifications are sent asynchronously
- Notifications are retained for 72 hours
- Failed deliveries are logged for investigation

## Testing Strategy

### 1. Test Categories
- Event Processing Tests
- Event Bus Tests
- Multiple Listener Tests
- Transaction Tests
- Error Cases

### 2. Test Infrastructure
```python
@pytest.fixture(autouse=True)
def configure_sync_mode(settings):
    settings.DJANGO_Q = {
        'sync': True,
        'timeout': 30,
        'save_limit': 0
    }
```

### 3. Testing Patterns
1. **Synchronous Flow Testing**:
   - Direct handler calls
   - Immediate assertion checking
   - Used for preference and template testing

2. **Test Helpers**:
```python
@pytest.fixture
def wait_for_notifications():
    def _wait(filter_kwargs, expected_count=1, timeout=10):
        start_time = time.time()
        while time.time() - start_time < timeout:
            count = NotifiableEvent.objects.filter(**filter_kwargs).count()
            if count == expected_count:
                return True
            time.sleep(min(sleep_time, 0.5))
        raise TimeoutError(f"Timed out waiting for {expected_count} notifications")
    return _wait
```

## Best Practices

### 1. Error Handling
- Graceful handling of missing templates
- Fallback error messages for template rendering failures
- Comprehensive error logging
- Transaction management

### 2. Performance
- Async processing via Django Q
- Efficient database queries
- Automatic cleanup of old records
- Distinct notifications for users with multiple roles

### 3. Maintainability
- Clear separation of concerns
- Template-based formatting
- Centralized event type registry
- Comprehensive test coverage

### 4. Reliability
- Event logging
- Error tracking
- Fallback notifications
- Transaction safety

## Usage Guidelines

### 1. Adding New Event Types
1. Add to EventTypes registry
2. Create notification templates
3. Implement event handler
4. Add appropriate tests

### 2. Creating Templates
1. Define permitted parameters
2. Implement validation
3. Create both app and email templates
4. Test parameter formatting

### 3. Error Handling
1. Log all errors comprehensively
2. Provide fallback notifications
3. Monitor failed deliveries
4. Implement retry mechanisms

### 4. Testing
1. Test all notification paths
2. Verify preference handling
3. Check error cases
4. Test async behavior