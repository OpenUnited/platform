from typing import Dict
import logging
from apps.capabilities.security.services import RoleService
from apps.capabilities.commerce.models import Organisation
from apps.engagement.models import NotifiableEvent
from apps.capabilities.talent.models import Person

logger = logging.getLogger(__name__)

def handle_product_created(payload: Dict) -> None:
    """
    Handle product creation notification
    Creates NotifiableEvents for:
    - Organisation owners and managers (for org products)
    - Product owner (for personal products)
    """
    logger.info(f"Processing product created event: {payload}")
    
    try:
        organisation_id = payload.get('organisation_id')
        person_id = payload.get('person_id')
        
        if organisation_id:
            # Handle org-owned product
            role_service = RoleService()
            organisation = Organisation.objects.get(id=organisation_id)
            org_managers = role_service.get_organisation_managers(organisation)
            
            for manager in org_managers:
                NotifiableEvent.objects.create(
                    event_type=NotifiableEvent.EventType.PRODUCT_CREATED,
                    person=manager,
                    params={
                        'name': payload['name'],
                        'url': payload['url']
                    }
                ).create_notifications()
                
        elif person_id:
            # Handle personally-owned product
            try:
                owner = Person.objects.get(id=person_id)
                NotifiableEvent.objects.create(
                    event_type=NotifiableEvent.EventType.PRODUCT_CREATED,
                    person=owner,
                    params={
                        'name': payload['name'],
                        'url': payload['url']
                    }
                ).create_notifications()
            except Person.DoesNotExist:
                logger.error(f"Product owner not found: {person_id}")
                
    except Exception as e:
        logger.error(f"Error processing product created event: {e}")