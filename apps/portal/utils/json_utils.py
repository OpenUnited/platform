from django.core.serializers.json import DjangoJSONEncoder
import logging
import json

logger = logging.getLogger(__name__)

class TreeJSONEncoder(DjangoJSONEncoder):
    def default(self, obj):
        if isinstance(obj, dict):
            # Create the base node structure
            result = {
                'name': str(obj.get('name', '')),
                'description': str(obj.get('description', '')),
                'lens_type': str(obj.get('lens_type', 'experience')),
                'children': []  # Always include children array
            }
            
            # Process children if they exist
            if 'children' in obj and isinstance(obj['children'], list):
                result['children'] = [
                    self.default(child) for child in obj['children']
                    if isinstance(child, dict)
                ]
                
                logger.info("TreeJSONEncoder processed children", extra={
                    'children_count': len(result['children']),
                    'children': json.dumps(result['children'], indent=2)
                })
            
            logger.info("TreeJSONEncoder node", extra={
                'input': json.dumps(obj, indent=2),
                'output': json.dumps(result, indent=2)
            })
            return result
            
        return super().default(obj)
