# Notification System Design

## Core Concepts

### Event-Driven Architecture
- Events are published when significant actions occur
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
- Creates appropriate notifications

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
The Django Q worker picks up the event and routes it to the appropriate handler. The handler determines who should be notified:
- For organization products: notify organization managers
- For personal products: notify the product owner

### Step 3: Notification Creation
The system:
1. Creates a NotifiableEvent record
2. Checks the recipient's notification preferences
3. Creates appropriate notifications (app and/or email) based on those preferences

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
- Controls notification channels per event type

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
    event_bus.publish('product.created', {
        'organisation_id': product.organisation_id,
        'person_id': product.person_id,
        'name': product.name,
        'url': product.get_absolute_url()
    })
`````

### 2. Handling Events

````python`
# apps/engagement/events.py

def handle_product_created(payload: Dict) -> None:
    """Handle product creation notification"""
    if organisation_id := payload.get('organisation_id'):
        # Notify org managers
        organisation = Organisation.objects.get(id=organisation_id)
        org_managers = RoleService.get_organisation_managers(organisation)
        
        for manager in org_managers:
            NotifiableEvent.objects.create(
                event_type=NotifiableEvent.EventType.PRODUCT_CREATED,
                person=manager,
                params={'name': payload['name'], 'url': payload['url']}
            ).create_notifications()
`````

### 3. Creating Notifications

````python`
# apps/engagement/models.py

class NotifiableEvent(TimeStampMixin):
    def create_notifications(self):
        """Creates notifications based on preference"""
        pref = self.person.notification_preferences
        channel = pref.get_channel_for_event(self.event_type)
        
        if channel in [self.Type.APPS, self.Type.BOTH]:
            template = AppNotificationTemplate.objects.get(event_type=self.event_type)
            AppNotification.objects.create(
                event=self,
                title=template.title_template.format(**self.params),
                message=template.message_template.format(**self.params)
`````

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
