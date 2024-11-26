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
  - Both channels (default)
  - None (opt-out)
- Preferences are stored per person
- Default preferences created on first notification (BOTH)
- Notifications are created based on preference type

### Notification Types
- **App Notifications**: Displayed in the web interface
- **Email Notifications**: Sent via email
- Both types use templates with parameter substitution
- Fallback notifications created when templates missing/invalid

### Data Lifecycle
- Transient records (events, notifications) have `delete_at` fields
- Automatic cleanup of old records (72-hour retention)
- Templates and preferences are permanent
- Failed deliveries logged with error details

## System Components

### 1. Event Bus
```python
class EventBus:
    - Singleton pattern implementation
    - Single-task processing per event
    - Maintains registry of event listeners
    - Logs events in EventLog model
    - Transaction-safe event processing
```

### 2. NotifiableEvent
- Records notification-worthy events
- Links events to specific persons
- Stores event parameters for template rendering
- Used by notification processor to create notifications

### 3. Notification Templates
```python
class AppNotificationTemplate:
    - event_type: CharField (matches EventTypes registry)
    - title: CharField
    - template: CharField

class EmailNotificationTemplate:
    - event_type: CharField
    - title: CharField
    - template: CharField
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
- Atomic transaction handling
- Template-based notification creation
- Error handling with fallback notifications
- Preference-based notification routing
- Default preference creation

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
        'productId': str(product.id),
        'name': product.name,
        'url': f'/products/{product.slug}/',
        'organisationId': str(product.organisation.id),
        'personId': str(person.id)
    })
```

### Step 2: Event Processing
The system uses a transaction-safe approach:

1. **Event Bus**:
   - Validates events against EventTypes registry
   - Logs events in EventLog model
   - Manages task queuing with atomic transactions
   - Handles sync/async execution configuration

2. **Event Handlers**:
```python
def handle_product_created(event_data):
    with transaction.atomic():
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
            
            process_notification(event_id=event.id)
```

### Step 3: Notification Creation
The system processes notifications atomically:
```python
def process_notification(event_id):
    try:
        with transaction.atomic():
            event = NotifiableEvent.objects.select_for_update().get(id=event_id)
            person = event.person
            
            # Get or create notification preferences with default BOTH
            prefs, created = NotificationPreference.objects.get_or_create(
                person=person,
                defaults={'product_notifications': NotificationPreference.Type.BOTH}
            )
            
            notification_type = prefs.product_notifications
            
            # Create app notifications if enabled
            if notification_type in [NotificationPreference.Type.APPS, NotificationPreference.Type.BOTH]:
                try:
                    template = AppNotificationTemplate.objects.get(event_type=event.event_type)
                    try:
                        title = template.title.format(**event.params)
                        message = template.template.format(**event.params)
                    except KeyError as e:
                        logger.error(f"Missing template parameter: {e}")
                        title = "Notification Error"
                        message = "There was an error processing this notification."
                    
                    AppNotification.objects.create(
                        event=event,
                        title=title,
                        message=message
                    )
                except AppNotificationTemplate.DoesNotExist:
                    logger.error(f"No app template found for event type: {event.event_type}")
                    AppNotification.objects.create(
                        event=event,
                        message="There was an error processing this notification."
                    )
            
            # Create email notifications if enabled
            if notification_type in [NotificationPreference.Type.EMAIL, NotificationPreference.Type.BOTH]:
                try:
                    template = EmailNotificationTemplate.objects.get(event_type=event.event_type)
                    try:
                        title = template.title.format(**event.params)
                        body = template.template.format(**event.params)
                    except KeyError as e:
                        logger.error(f"Missing template parameter: {e}")
                        title = "Notification Error"
                        body = "There was an error processing this notification."
                    
                    EmailNotification.objects.create(
                        event=event,
                        title=title,
                        body=body
                    )
                except EmailNotificationTemplate.DoesNotExist:
                    logger.error(f"No email template found for event type: {event.event_type}")
                    EmailNotification.objects.create(
                        event=event,
                        title="System Notification",
                        body="A notification was generated but the template was not found."
                    )
            
            return True
    except Exception as e:
        logger.error(f"Error processing notification: {str(e)}")
        return False
```

## Testing Strategy

### 1. Test Categories
- Event Processing Tests with sync execution
- Transaction safety tests
- Multiple stakeholder notification tests
- Template rendering and fallback tests
- Default preference creation tests

### 2. Test Infrastructure
```python
@pytest.fixture(autouse=True)
def configure_sync_mode(settings):
    """Configure Django-Q for synchronous execution"""
    settings.DJANGO_Q = {
        'sync': True,
        'timeout': 30,
        'save_limit': 0
    }
    
    settings.EVENT_BUS = {
        'BACKEND': 'apps.event_hub.services.backends.django_q.DjangoQBackend',
        'TASK_COMPLETE_HOOK': None  # Disable the hook in sync mode
    }
```

### 3. Testing Patterns
1. **Transaction Testing**:
   - Use `@pytest.mark.django_db(transaction=True)`
   - Test atomic operations
   - Verify rollback behavior
   - Ensure notification consistency

2. **Notification Creation Testing**:
```python
@pytest.mark.django_db(transaction=True)
def test_async_notification_processing(
    self, transactional_db, person, event_data, notification_preferences,
    notification_templates
):
    event_bus = get_event_bus()
    
    # Commit fixture data
    transaction.commit()
    
    event_bus.publish(EventTypes.PRODUCT_CREATED, event_data)
    
    # Verify notifications
    assert AppNotification.objects.filter(event__person=person).exists()
    assert EmailNotification.objects.filter(event__person=person).exists()
```

## Best Practices

### 1. Error Handling
- Catch and log all template rendering errors
- Create fallback notifications for all failure cases
- Use atomic transactions for consistency
- Log detailed error information

### 2. Performance
- Select related fields in queries
- Use atomic transactions for consistency
- Create notifications efficiently
- Handle multiple stakeholders distinctly
- Ensure distinct notifications for users with multiple roles

### 3. Maintainability
- Clear separation of notification types
- Template-based message formatting
- Centralized event registry
- Comprehensive test coverage

### 4. Reliability
- Transaction safety guarantees
- Fallback notifications
- Default preferences
- Error logging and monitoring

## Usage Guidelines

### 1. Adding New Event Types
1. Add to EventTypes registry
2. Create notification templates
3. Implement event handler
4. Add transaction-safe tests

### 2. Creating Templates
1. Define template parameters
2. Implement safe parameter substitution
3. Create both app and email templates
4. Test rendering and fallbacks

### 3. Error Handling
1. Implement fallback notifications
2. Use atomic transactions
3. Log detailed error information
4. Test error scenarios

### 4. Testing
1. Test transaction safety
2. Verify notification creation
3. Check template rendering
4. Test preference handling
5. Verify stakeholder notifications