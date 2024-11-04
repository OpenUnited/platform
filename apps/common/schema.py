"""
Platform Schema Documentation
"""

from django.apps import apps
from django.db import models
from django.utils.translation import gettext_lazy as _
from typing import Dict, Any
import json
import inspect


class SchemaEncoder(json.JSONEncoder):
    """Custom JSON encoder to handle Django's lazy translation objects."""
    def default(self, obj):
        if isinstance(obj, type):
            return str(obj)
        if hasattr(obj, '__str__'):
            return str(obj)
        return super().default(obj)


def get_inheritance_info(model) -> Dict[str, Any]:
    """Get model inheritance information."""
    inheritance = {
        'type': 'concrete',  # default
        'parents': [],
        'children': []
    }
    
    # Get parent models
    for base in model.__bases__:
        if hasattr(base, '_meta') and not base._meta.abstract:
            inheritance['parents'].append({
                'model': base.__name__,
                'app': base._meta.app_label if hasattr(base._meta, 'app_label') else None
            })
    
    # Check if this is a proxy model
    if model._meta.proxy:
        inheritance['type'] = 'proxy'
        inheritance['proxy_for'] = {
            'model': model._meta.proxy_for_model.__name__,
            'app': model._meta.proxy_for_model._meta.app_label
        }
    
    # Check if this is an abstract base class
    elif model._meta.abstract:
        inheritance['type'] = 'abstract'
    
    return inheritance


def get_reverse_relationships(model) -> Dict[str, Any]:
    """Get model's reverse relationships."""
    reverse_relations = {}
    
    for relation in model._meta.get_fields():
        if relation.auto_created and not relation.concrete:
            # This is a reverse relation
            try:
                reverse_relations[relation.name] = {
                    'type': type(relation).__name__,
                    'model': relation.related_model.__name__,
                    'app': relation.related_model._meta.app_label,
                    'related_name': getattr(relation.remote_field, 'related_name', None),
                    'related_query_name': getattr(relation.remote_field, 'related_query_name', lambda: None)(),
                    'many_to_many': getattr(relation, 'many_to_many', False),
                    'one_to_many': getattr(relation, 'one_to_many', False),
                    'one_to_one': getattr(relation, 'one_to_one', False),
                }
            except AttributeError as e:
                # If we can't get some attributes, still include basic relationship info
                reverse_relations[relation.name] = {
                    'type': type(relation).__name__,
                    'model': relation.related_model.__name__,
                    'app': relation.related_model._meta.app_label,
                }
    
    return reverse_relations


def generate_schema() -> Dict[str, Any]:
    """Generate a complete schema of all models in the platform."""
    schema = {}
    
    for model in apps.get_models():
        app_label = model._meta.app_label
        model_name = model.__name__
        
        if app_label not in schema:
            schema[app_label] = {}
            
        # Get model fields
        fields = {}
        for field in model._meta.get_fields():
            field_info = {
                'type': field.get_internal_type() if hasattr(field, 'get_internal_type') else str(type(field).__name__),
                'null': getattr(field, 'null', None),
                'blank': getattr(field, 'blank', None),
                'help_text': str(getattr(field, 'help_text', '')),
                'choices': dict(field.choices) if getattr(field, 'choices', None) else None,
            }
            
            # Add foreign key references
            if isinstance(field, models.ForeignKey):
                field_info['references'] = {
                    'model': field.related_model.__name__,
                    'app': field.related_model._meta.app_label,
                    'on_delete': str(field.remote_field.on_delete.__name__),
                }
            
            # Add many-to-many references
            elif isinstance(field, models.ManyToManyField):
                field_info['references'] = {
                    'model': field.related_model.__name__,
                    'app': field.related_model._meta.app_label,
                    'through': field.remote_field.through.__name__ if field.remote_field.through else None,
                }
            
            fields[field.name] = field_info

        # Get model methods
        methods = {}
        for name, method in inspect.getmembers(model, predicate=inspect.isfunction):
            if not name.startswith('_'):  # Skip private methods
                methods[name] = {
                    'doc': str(inspect.getdoc(method)),
                    'signature': str(inspect.signature(method)),
                }

        # Get meta options
        meta_options = {}
        if hasattr(model, '_meta'):
            meta = model._meta
            meta_options = {
                'ordering': getattr(meta, 'ordering', None),
                'unique_together': getattr(meta, 'unique_together', None),
                'verbose_name': str(meta.verbose_name),
                'verbose_name_plural': str(meta.verbose_name_plural),
                'abstract': meta.abstract,
                'db_table': meta.db_table,
            }
                
        schema[app_label][model_name] = {
            'fields': fields,
            'methods': methods,
            'meta': meta_options,
            'inheritance': get_inheritance_info(model),
            'reverse_relations': get_reverse_relationships(model),
            'doc': str(model.__doc__),
            'app_label': app_label,
        }
    
    return schema


def save_schema(path: str = 'apps/common/schema.json') -> None:
    """Generate and save schema to a JSON file."""
    try:
        schema = generate_schema()
        with open(path, 'w') as f:
            json.dump(schema, f, indent=2, cls=SchemaEncoder)
    except Exception as e:
        raise Exception(f"Failed to save schema: {str(e)}")


def load_schema(path: str = 'apps/common/schema.json') -> Dict[str, Any]:
    """Load schema from JSON file."""
    try:
        with open(path) as f:
            return json.load(f)
    except Exception as e:
        raise Exception(f"Failed to load schema: {str(e)}")
