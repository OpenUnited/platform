# AI Factory Service Documentation

## Overview

The AI Factory provides AI-powered content generation services across the platform, starting with automated product creation. It uses OpenAI's API to transform minimal input into structured product information, integrating with the platform's event-driven architecture and quota management systems.

## Core Components

### Directory Structure
```
apps/
  event_hub/
    events.py              # Central event registry
  capabilities/
    commerce/
      models/
        quotas.py         # Quota models
      services/
        quota_service.py  # Quota management
    ai_factory/
      apps.py            # Event registration
      handlers.py        # Event handlers
      services/
        generation.py    # AI generation
        security.py      # Input validation
      prompts/
        product.py       # AI prompts
```

### Event Registry

```python
# apps/event_hub/events.py
class EventTypes:
    """Central registry of all application events"""
    
    # Product Events
    PRODUCT_CREATED = 'product.created'
    PRODUCT_UPDATED = 'product.updated'
    PRODUCT_DELETED = 'product.deleted'
    
    # AI Factory Events
    AI_PRODUCT_GENERATION_REQUESTED = 'ai.product.generation.requested'
    AI_PRODUCT_GENERATION_COMPLETED = 'ai.product.generation.completed'
    AI_PRODUCT_GENERATION_FAILED = 'ai.product.generation.failed'
    
    # Display names for events
    DISPLAY_NAMES = {
        PRODUCT_CREATED: "Product Created",
        PRODUCT_UPDATED: "Product Updated",
        PRODUCT_DELETED: "Product Deleted",
        AI_PRODUCT_GENERATION_REQUESTED: "AI Product Generation Requested",
        AI_PRODUCT_GENERATION_COMPLETED: "AI Product Generation Completed",
        AI_PRODUCT_GENERATION_FAILED: "AI Product Generation Failed",
    }

    @classmethod
    def validate_event(cls, event_name: str) -> bool:
        """Validate if an event name is registered"""
        return event_name in cls.DISPLAY_NAMES
```

### Quota Management Models

```python
# apps/capabilities/commerce/models/quotas.py
from django.db import models
from django.utils import timezone
from django.core.validators import MinValueValidator

class OrganisationQuota(models.Model):
    """Tracks service quotas per organisation"""
    class QuotaType(models.TextChoices):
        AI_REQUESTS = "AI_REQUESTS", "AI Requests"
        API_CALLS = "API_CALLS", "API Calls"

    organisation = models.ForeignKey(
        'commerce.Organisation',
        on_delete=models.CASCADE,
        related_name='quotas'
    )
    quota_type = models.CharField(
        max_length=50,
        choices=QuotaType.choices
    )
    monthly_limit = models.IntegerField(
        default=1000,
        validators=[MinValueValidator(0)]
    )
    is_unlimited = models.BooleanField(default=False)

    class Meta:
        unique_together = ['organisation', 'quota_type']
        indexes = [
            models.Index(fields=['organisation', 'quota_type'])
        ]

class QuotaUsage(models.Model):
    """Tracks monthly service usage"""
    organisation = models.ForeignKey(
        'commerce.Organisation',
        on_delete=models.CASCADE,
        related_name='quota_usage'
    )
    quota_type = models.CharField(
        max_length=50,
        choices=OrganisationQuota.QuotaType.choices
    )
    month = models.DateField()
    requests_count = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0)]
    )
    usage_data = models.JSONField(default=dict)

    class Meta:
        unique_together = ['organisation', 'quota_type', 'month']
```

### Quota Service

```python
# apps/capabilities/commerce/services/quota_service.py
from typing import Optional
from django.utils import timezone
from django.db import transaction
from apps.capabilities.commerce.models import OrganisationQuota, QuotaUsage

class QuotaExceededError(Exception):
    pass

class QuotaService:
    def __init__(self, quota_type: str, default_monthly_limit: int):
        self.quota_type = quota_type
        self.default_monthly_limit = default_monthly_limit

    def check_quota_available(self, organisation_id: str) -> bool:
        try:
            quota = OrganisationQuota.objects.get(
                organisation_id=organisation_id,
                quota_type=self.quota_type
            )
            if quota.is_unlimited:
                return True
                
            usage = QuotaUsage.get_current_usage(
                organisation_id, 
                self.quota_type
            )
            return usage.requests_count < quota.monthly_limit
            
        except OrganisationQuota.DoesNotExist:
            usage = QuotaUsage.get_current_usage(
                organisation_id, 
                self.quota_type
            )
            return usage.requests_count < self.default_monthly_limit

    def increment_usage(self, 
                       organisation_id: str, 
                       additional_data: Optional[dict] = None) -> None:
        with transaction.atomic():
            usage = QuotaUsage.get_current_usage(
                organisation_id, 
                self.quota_type
            )
            usage = QuotaUsage.objects.select_for_update().get(id=usage.id)
            
            try:
                quota = OrganisationQuota.objects.get(
                    organisation_id=organisation_id,
                    quota_type=self.quota_type
                )
                limit = quota.monthly_limit if not quota.is_unlimited else None
            except OrganisationQuota.DoesNotExist:
                limit = self.default_monthly_limit
                
            if limit and usage.requests_count >= limit:
                raise QuotaExceededError(
                    f"Monthly quota of {limit} requests exceeded"
                )
            
            usage.requests_count += 1
            if additional_data:
                usage.usage_data.update(additional_data)
            usage.save()
```

### AI Factory Components

```python
# apps/capabilities/ai_factory/apps.py
from django.apps import AppConfig
from apps.event_hub import get_event_bus
from apps.event_hub.events import EventTypes

class AIFactoryConfig(AppConfig):
    name = 'apps.capabilities.ai_factory'
    
    def ready(self):
        event_bus = get_event_bus()
        
        from .handlers import (
            handle_product_generation_request,
            handle_generation_completed,
            handle_generation_failed
        )
        
        event_bus.register_listener(
            EventTypes.AI_PRODUCT_GENERATION_REQUESTED,
            handle_product_generation_request
        )
        event_bus.register_listener(
            EventTypes.AI_PRODUCT_GENERATION_COMPLETED,
            handle_generation_completed
        )
        event_bus.register_listener(
            EventTypes.AI_PRODUCT_GENERATION_FAILED,
            handle_generation_failed
        )

# apps/capabilities/ai_factory/security.py
import re
from typing import Dict

def sanitize_input(user_input: str) -> str:
    """Sanitize user input to prevent prompt injection"""
    sanitized = re.sub(
        r"(system:|assistant:|ignore previous|ignore above)", 
        "", 
        user_input,
        flags=re.IGNORECASE
    )
    return sanitized.replace("\n", " ").strip()

def validate_content(content: Dict) -> bool:
    """Validate AI-generated content"""
    if not all(k in content for k in ['name', 'description']):
        return False
        
    # Add specific validation rules
    return True

# apps/capabilities/ai_factory/services/generation.py
from django.conf import settings
from openai import OpenAI
from apps.capabilities.commerce.services.quota_service import QuotaService
from apps.capabilities.ai_factory.security import sanitize_input, validate_content

class GenerationService:
    def __init__(self):
        self.client = OpenAI(api_key=settings.OPENAI_API_KEY)
        self.quota_service = QuotaService(
            quota_type='AI_REQUESTS',
            default_monthly_limit=settings.DEFAULT_AI_MONTHLY_LIMIT
        )

    def generate_product_content(self, 
                               organisation_id: str,
                               input_data: Dict) -> Dict:
        # Check quota
        if not self.quota_service.check_quota_available(organisation_id):
            raise QuotaExceededError()

        # Sanitize input
        sanitized_input = {
            k: sanitize_input(str(v))
            for k, v in input_data.items()
        }

        # Generate via OpenAI
        response = self.client.chat.completions.create(
            model="gpt-4",
            messages=[{
                "role": "user",
                "content": self._build_prompt(sanitized_input)
            }],
            timeout=90
        )

        content = self._parse_response(response)
        
        if not validate_content(content):
            raise InvalidContentError()

        # Record usage
        self.quota_service.increment_usage(
            organisation_id=organisation_id,
            additional_data={
                'tokens_used': response.usage.total_tokens
            }
        )

        return content

# apps/capabilities/ai_factory/handlers.py
from typing import Dict
from apps.event_hub import get_event_bus
from apps.event_hub.events import EventTypes
from apps.capabilities.ai_factory.services.generation import GenerationService

def handle_product_generation_request(event_type: str, payload: Dict) -> None:
    """Handle product generation request events"""
    service = GenerationService()
    
    try:
        content = service.generate_product_content(
            organisation_id=payload['organisation_id'],
            input_data=payload['input_data']
        )
        
        product = create_product_from_content(content)
        
        event_bus = get_event_bus()
        event_bus.publish(
            EventTypes.AI_PRODUCT_GENERATION_COMPLETED,
            {
                'task_id': payload['task_id'],
                'product_id': str(product.id),
                'organisation_id': payload['organisation_id']
            }
        )
    
    except Exception as e:
        event_bus = get_event_bus()
        event_bus.publish(
            EventTypes.AI_PRODUCT_GENERATION_FAILED,
            {
                'task_id': payload['task_id'],
                'error': str(e),
                'organisation_id': payload['organisation_id']
            }
        )
```

## Usage Examples

### 1. Request Product Generation
```python
def request_product_generation(organisation_id: str, 
                             product_data: Dict) -> None:
    event_bus = get_event_bus()
    
    event_bus.publish(
        EventTypes.AI_PRODUCT_GENERATION_REQUESTED,
        {
            'task_id': str(uuid.uuid4()),
            'organisation_id': organisation_id,
            'input_data': product_data
        }
    )
```

### 2. Check Organisation Usage
```python
def get_ai_usage(organisation_id: str) -> Dict:
    usage = QuotaUsage.get_current_usage(
        organisation_id=organisation_id,
        quota_type=OrganisationQuota.QuotaType.AI_REQUESTS
    )
    
    return {
        'requests_used': usage.requests_count,
        'tokens_used': usage.usage_data.get('tokens_used', 0)
    }
```

## Security Considerations

1. **Input Validation**
   - Prompt injection prevention
   - Content sanitisation
   - Length limits

2. **Output Validation**
   - Content safety checks
   - Structure validation
   - Response size limits

## Monitoring

1. **Key Metrics**
   - Generation success rate
   - API latency
   - Token usage
   - Error rates
   - Quota utilisation

2. **Alerting**
   - High error rates
   - Quota thresholds
   - Security violations
   - API issues

## Future Enhancements

1. **Phase 1 (Current)**
   - Basic product generation
   - Essential security
   - Usage tracking

2. **Phase 2**
   - Enhanced content validation
   - Advanced quota management
   - Usage analytics

3. **Phase 3**
   - Multi-provider support
   - Content caching
   - Cost optimisation

Would you like me to expand on any part of this documentation?