"""
Management command to generate human-readable schema documentation.
"""

import os
from django.core.management.base import BaseCommand
from apps.common.schema import load_schema


class SchemaDocumentationGenerator:
    def __init__(self, schema_data):
        self.schema = schema_data
        self.app_groups = {
            'Core': ['product_management'],
            'Users': ['security', 'auth'],
            'Payments': ['commerce'],
            'Talent': ['talent'],
        }
        self.model_groups = {
            'Core Business': ['Product', 'Challenge', 'Bounty', 'Initiative'],
            'User Management': ['Person', 'User', 'Group'],
            'Skills & Expertise': ['Skill', 'Expertise', 'PersonSkill'],
            'Payments': ['OrganisationAccount', 'ContributorAccount', 'Grant'],
        }
    
    def generate_markdown(self) -> str:
        """Generate focused, valuable documentation."""
        sections = [
            "# Platform Schema Documentation\n",
            "## Overview\n",
            self._generate_overview(),
            "## Core Concepts\n",
            self._generate_core_concepts(),
            self._generate_app_groups(),
        ]
        return "\n".join(filter(None, sections))
    
    def _generate_overview(self) -> str:
        return """
This document outlines the key models and their relationships in the platform.

### Key Areas
- **Products & Challenges**: Core business objects
- **Users & Organizations**: Account management
- **Payments & Rewards**: Financial transactions
- **Skills & Expertise**: Talent management
"""

    def _generate_core_concepts(self) -> str:
        return """
### Product Flow
```mermaid
graph LR
    Organisation --> Product
    Product --> Challenge
    Challenge --> Bounty
    Bounty --> BountyClaim
```

### Payment Flow
```mermaid
graph LR
    Organisation --> OrganisationAccount
    OrganisationAccount --> ProductAccount
    ProductAccount --> BountyClaim
```
"""

    def _generate_app_groups(self) -> str:
        """Generate documentation sections grouped by functionality."""
        sections = []
        
        # Generate grouped sections
        for group_name, apps in self.app_groups.items():
            group_models = []
            for app_name in apps:
                if app_name in self.schema:
                    group_models.extend([
                        (app_name, model_name, model_data)
                        for model_name, model_data in self.schema[app_name].items()
                    ])
            
            if group_models:
                sections.extend([
                    f"## {group_name}\n",
                    self._generate_group_er_diagram(group_models),
                    *[self._generate_model_documentation(app, model, data) 
                      for app, model, data in sorted(group_models, key=lambda x: x[1])],
                ])
        
        return "\n".join(filter(None, sections))

    def _generate_group_er_diagram(self, models) -> str:
        """Generate focused ER diagram showing only key relationships."""
        diagram = [
            "### Key Relationships\n",
            "```mermaid",
            "erDiagram"
        ]
        
        # Show only important fields (no IDs, timestamps etc)
        important_field_types = ['CharField', 'TextField', 'IntegerField', 'ForeignKey', 'ManyToManyField']
        
        for app_name, model_name, model_data in models:
            key_fields = [
                f"{name} {info['type']}" 
                for name, info in model_data['fields'].items()
                if (info['type'] in important_field_types and 
                    not name.startswith('_') and 
                    name not in ('id', 'created_at', 'updated_at'))
            ][:3]  # Limit to 3 most important fields
            
            if key_fields:
                diagram.append(f"    {model_name} {{")
                for field in key_fields:
                    diagram.append(f"        {field}")
                diagram.append("    }")
        
        # Show only direct relationships
        for app_name, model_name, model_data in models:
            for field_name, field_info in model_data['fields'].items():
                if ('references' in field_info and 
                    field_info['references']['model'] in [m[1] for m in models]):
                    cardinality = "||--o{" if field_info['type'] == 'ForeignKey' else "}|--||"
                    diagram.append(f"    {model_name} {cardinality} {field_info['references']['model']} : \"\"")
        
        diagram.append("```\n")
        return "\n".join(diagram)

    def _generate_model_documentation(self, app_name: str, model_name: str, model_data: dict) -> str:
        """Generate focused documentation for a model."""
        sections = [
            f"### {model_name}\n",
            self._generate_model_purpose(model_name),
            self._generate_key_fields(model_data),
            self._generate_key_relationships(model_data),
            self._generate_meta_info(model_data),
        ]
        return "\n".join(filter(None, sections))

    def _generate_model_purpose(self, model_name: str) -> str:
        """Generate clear purpose description for each model."""
        purposes = {
            'Product': 'Represents a product in the platform that organizations can create and manage.',
            'Challenge': 'Represents a specific task or goal within a product that needs to be accomplished.',
            'Bounty': 'Represents a reward offered for completing a specific challenge.',
            'Person': 'Represents a user profile with their skills and contributions.',
            # Add more as needed
        }
        return purposes.get(model_name, '')

    def _generate_key_fields(self, model_data: dict) -> str:
        """Generate documentation for important fields only."""
        fields = model_data.get('fields', {})
        important_fields = {
            name: info for name, info in fields.items()
            if not name.startswith('_') 
            and name not in ('id', 'created_at', 'updated_at')
            and (info.get('help_text') or info.get('choices') or 'references' in info)
        }
        
        if not important_fields:
            return ""
            
        table = [
            "#### Key Fields",
            "| Field | Type | Description | Rules |",
            "|-------|------|-------------|--------|"
        ]
        
        for name, info in sorted(important_fields.items()):
            rules = []
            if info.get('choices'):
                rules.append(f"Choices: {', '.join(info['choices'].values())}")
            if 'references' in info:
                rules.append(f"References: {info['references']['model']}")
            if not info.get('null'):
                rules.append("Required")
                
            table.append(
                f"| {name} | {info['type']} | "
                f"{info['help_text'] or '_No description_'} | "
                f"{', '.join(rules) or '_None_'} |"
            )
        
        return "\n".join(table) + "\n"

    def _generate_key_relationships(self, model_data: dict) -> str:
        """Generate clear relationship documentation."""
        relationships = []
        
        # Direct relationships
        for field_name, field_info in model_data.get('fields', {}).items():
            if 'references' in field_info:
                rel_type = "Has One" if field_info['type'] == 'OneToOneField' else "References"
                relationships.append(
                    f"- **{rel_type}** {field_info['references']['model']}"
                )
        
        # Reverse relationships
        for rel_name, rel_info in model_data.get('reverse_relations', {}).items():
            if rel_info.get('one_to_many'):
                relationships.append(f"- **Has Many** {rel_info['model']}")
            elif rel_info.get('many_to_many'):
                relationships.append(f"- **Many to Many** {rel_info['model']}")
        
        if relationships:
            return "#### Relationships\n" + "\n".join(relationships) + "\n"
        return ""

    def _generate_meta_info(self, model_data: dict) -> str:
        """Generate important meta information."""
        meta = model_data.get('meta', {})
        info = []
        
        if meta.get('unique_together'):
            info.append(f"- **Unique Together:** {meta['unique_together']}")
        if meta.get('ordering'):
            info.append(f"- **Default Ordering:** {meta['ordering']}")
        if meta.get('indexes'):
            info.append(f"- **Indexes:** {meta['indexes']}")
        
        if info:
            return "#### Meta\n" + "\n".join(info) + "\n"
        return ""


class Command(BaseCommand):
    """Django command to generate schema documentation."""
    
    help = 'Generates human-readable schema documentation with ER diagrams'

    def handle(self, *args, **options):
        try:
            # Load schema
            schema = load_schema()
            
            # Generate documentation
            generator = SchemaDocumentationGenerator(schema)
            documentation = generator.generate_markdown()
            
            # Save to docs/schema.md
            os.makedirs('docs', exist_ok=True)
            with open('docs/schema.md', 'w') as f:
                f.write(documentation)
                
            self.stdout.write(
                self.style.SUCCESS(
                    'Successfully generated schema documentation at docs/schema.md'
                )
            )
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Failed to generate documentation: {str(e)}')
            )