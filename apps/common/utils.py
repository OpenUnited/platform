import uuid
from django import forms

class BaseModelForm(forms.ModelForm):
    """
    Base form class with common functionality for all model forms.
    
    Features:
    - Common validation methods
    - Error handling utilities
    - Form field utilities
    """
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.error_messages = {}

    def add_error_message(self, field, message):
        """Add an error message for a specific field"""
        if field not in self.error_messages:
            self.error_messages[field] = []
        self.error_messages[field].append(message)

    def clean(self):
        """Common validation logic for all forms"""
        cleaned_data = super().clean()
        return cleaned_data

    def is_valid(self):
        """Extended validation including custom error messages"""
        is_valid = super().is_valid()
        
        # Add custom error messages to form errors
        for field, messages in self.error_messages.items():
            for message in messages:
                self.add_error(field, message)
                
        return is_valid and not bool(self.error_messages)
    

def serialize_tree(node):
    """Serializer for the tree."""
    return {
        "id": node.pk,
        "node_id": uuid.uuid4(),
        "name": node.name,
        "description": node.description,
        "video_link": node.video_link,
        "video_name": node.video_name,
        "video_duration": node.video_duration,
        "has_saved": True,
        "children": [serialize_tree(child) for child in node.get_children()],
    }
