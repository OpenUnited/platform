from django.template import Template, Context, TemplateSyntaxError
from django.template.loader import get_template
from django.test import RequestFactory
from pathlib import Path
from typing import Dict, List, Tuple, Any, Union, Callable
import re
import os

class TemplateConverter:
    def __init__(self):
        self.request_factory = RequestFactory()
        
        # Define standalone and closing patterns first since they're used in validation
        self.standalone_tags = {
            'load', 'csrf_token', 'spaceless', 'url', 'static', 'trans',
            'blocktrans', 'blocktranslate', 'autoescape', 'cycle',
            'firstof', 'regroup', 'add_preserved_filters', 'paginator_number',
            'get_admin_log', 'endget_admin_log', 'admin_actions'
        }
        
        self.conversion_patterns = {
            # Convert Jinja2 imports to Django load tags
            r'{%\s*import\s+[\'"]([^\'"]+)[\'"]\s+as\s+\w+\s*%}': r'{% load \1 %}',
            
            # URL conversion
            r'{{\s*url_for\([\'"]([^\'"]+)[\'"]\s*(?:,\s*(.+?))?\)\s*}}': lambda m: self._convert_url_pattern(m),
            
            # Static file handling
            r'{{\s*static\([\'"]([^\'"]+)[\'"]\)\s*}}': r"{% static '\1' %}",
            
            # Filter conversion
            r'\|datetime': r'|date',  # Convert datetime filter to date
            r'\|capitalize': r'|capfirst',  # Convert capitalize to capfirst
            r'\|default\((.*?)\)': r'|default:\1',  # Convert default filter
            
            # Template inheritance
            r'{%\s*extends\s+"([^"]+)"\s*%}': r"{% extends '\1' %}",
            r'{%\s*include\s+"([^"]+)"\s*%}': r"{% include '\1' %}",
            
            # Comments
            r'{#(.+?)#}': r'{% comment %}\1{% endcomment %}',
            
            # Expressions
            r'{{\s*(.+?)\s*}}': self._convert_expression,
        }

    def _convert_url_pattern(self, match) -> str:
        """Convert Jinja2 url_for to Django url tag"""
        url_name = match.group(1)
        args = match.group(2) if match.group(2) else ''
        
        if args:
            # Convert Jinja2 keyword arguments to Django URL arguments
            args = args.strip()
            if '=' in args:
                # Convert kwargs to Django syntax
                kwargs = [f"{k.strip()}={v.strip()}" for k, v in 
                         (pair.split('=') for pair in args.split(','))]
                return f"{{% url '{url_name}' {' '.join(kwargs)} %}}"
            else:
                # Convert positional args
                return f"{{% url '{url_name}' {args} %}}"
        
        return f"{{% url '{url_name}' %}}"

    def _convert_expression(self, match) -> str:
        """Convert Jinja2 expressions to Django template syntax"""
        expr = match.group(1)
        # Convert common Jinja2 expressions to Django syntax
        expr = expr.replace('.items()', '.items')
        expr = expr.replace('.keys()', '.keys')
        expr = expr.replace('.values()', '.values')
        return f"{{{{ {expr} }}}}"

    def _convert_url_patterns(self, content: str) -> str:
        """Convert various URL patterns to Django syntax"""
        patterns = [
            # url() with kwargs and args
            (r'{{\s*url\([\'"]([^\'"]+)[\'"]\s*,\s*args=\((.*?)\)\s*,\s*kwargs=\{(.*?)\}\s*\)\s*}}',
             r"{% url '\1' \2 \3 %}"),
            
            # url() with just args
            (r'{{\s*url\([\'"]([^\'"]+)[\'"]\s*,\s*args=\((.*?)\)\s*\)\s*}}',
             r"{% url '\1' \2 %}"),
            
            # url() with just kwargs
            (r'{{\s*url\([\'"]([^\'"]+)[\'"]\s*,\s*kwargs=\{(.*?)\}\s*\)\s*}}',
             r"{% url '\1' \2 %}"),
            
            # url() with namespace
            (r'{{\s*url\([\'"](\w+):([^\'"]+)[\'"]\s*\)\s*}}',
             r"{% url '\1:\2' %}"),
            
            # Simple url()
            (r'{{\s*url\([\'"]([^\'"]+)[\'"]\)\s*}}',
             r"{% url '\1' %}"),
            
            # url() with string concatenation
            (r'{{\s*url\(([^\'"]+)\s*\+\s*[\'"]([^\'"]+)[\'"]\s*\)\s*}}',
             r"{% url \1\2 %}"),
        ]
        
        for pattern, replacement in patterns:
            content = re.sub(pattern, replacement, content)
        
        return content

    def _convert_template_tags(self, content: str) -> str:
        """Convert template tag syntax and ensure proper loading"""
        required_loads = set()
        
        # Base tags that need to be loaded
        base_tags = {
            'static': 'static',
            'i18n': 'i18n',
            'l10n': 'l10n',
            'cache': 'cache',
            'crispy_forms_tags': 'crispy_forms_tags',
            'admin_list': 'admin_list',
            'admin_modify': 'admin_modify',
            'admin_urls': 'admin_urls',
            'admin_tree': 'admin_tree',
            'admin_tree_list': 'admin_tree_list'
        }
        
        # Add required loads based on content
        for tag, library in base_tags.items():
            if tag in content:
                required_loads.add(library)
        
        # Add load statements at the top
        if required_loads:
            load_statements = '\n'.join(f"{{% load {lib} %}}" for lib in sorted(required_loads))
            content = f"{load_statements}\n{content}"
        
        return content

    def _fix_unclosed_tags(self, content: str) -> str:
        """Fix unclosed template tags"""
        # Track opening and closing tags
        tag_stack = []
        
        # Find all template tags
        tag_pattern = r'{%\s*([^%}]+)\s*%}'
        matches = re.finditer(tag_pattern, content)
        
        for match in matches:
            tag = match.group(1).strip().split()[0]
            if tag in ['if', 'for', 'block', 'with']:
                tag_stack.append(tag)
            elif tag in ['endif', 'endfor', 'endblock', 'endwith']:
                if tag_stack and tag_stack[-1] == tag[3:]:
                    tag_stack.pop()
        
        # Add missing closing tags
        while tag_stack:
            tag = tag_stack.pop()
            content += f'{{% end{tag} %}}'
            
        return content

    def _convert_set_statements(self, content: str) -> str:
        """Convert Jinja2 set statements to Django with tags"""
        # Convert set statements to with tags
        content = re.sub(
            r'{%\s*set\s+(\w+)\s*=\s*(.*?)\s*%}',
            r'{% with \1=\2 %}',
            content
        )
        
        # Add missing endwith tags
        content = self._fix_unclosed_tags(content)
        
        return content

    def _convert_boolean_operators(self, content: str) -> str:
        """Convert Jinja2 boolean operators to Django syntax"""
        # Convert == True/False
        content = re.sub(r'==\s*True\b', r'', content)
        content = re.sub(r'==\s*False\b', r' not ', content)
        
        # Convert is True/False
        content = re.sub(r'\bis\s+True\b', r'', content)
        content = re.sub(r'\bis\s+False\b', r' not ', content)
        
        return content

    def _convert_function_calls(self, content: str) -> str:
        """Convert Jinja2 function calls to Django template syntax"""
        # Convert method calls with parentheses to filters
        content = re.sub(
            r'\.([a-zA-Z_]+)\(\)',
            r'|\1',
            content
        )
        return content

    def convert_template(self, content: str) -> str:
        """Convert template content from Jinja2 to Django template syntax"""
        # Apply all conversion patterns
        for pattern, replacement in self.conversion_patterns.items():
            if callable(replacement):
                content = re.sub(pattern, replacement, content)
            else:
                content = re.sub(pattern, replacement, content)
        
        # Apply additional conversions
        content = self._convert_function_calls(content)
        content = self._convert_macro_syntax(content)
        content = self._convert_blocks(content)
        content = self._convert_control_structures(content)
        content = self._convert_static_tags(content)
        
        return content

class StagedConverter:
    def __init__(self, template_path: Path, output_dir: Path):
        # Convert string paths to Path objects if needed
        self.template_path = Path(template_path) if isinstance(template_path, str) else template_path
        self.output_dir = Path(output_dir) if isinstance(output_dir, str) else output_dir
        
        # Keep existing configuration
        self.required_libraries = {
            'admin_tree_list': 'django.contrib.admin.templatetags.admin_tree_list',
            'crispy_forms_tags': 'crispy_forms.templatetags.crispy_forms_tags',
            'custom_filters': 'apps.common.templatetags.custom_filters',
            'static': 'django.templatetags.static',
            'i18n': 'django.templatetags.i18n',
        }
        
        self.conversion_patterns = {
            'variable': (r'\{\{\s*([^}]+)\s*\}\}', r'{{ \1 }}'),
            'comment': (r'\{#\s*([^#}]+)\s*#\}', r'{# \1 #}'),
            'block': (r'\{%\s*([^%}]+)\s*%\}', r'{% \1 %}'),
        }
        
        self.fixes = [
            (r"url\('([^']+)',\s*args=\(([^)]+)\)\)", r"url '\1' \2"),
            (r"url\('([^']+)'\)", r"url '\1'"),
            (r"static\('([^']+)'\)", r"static '\1'"),
            (r"\.([a-zA-Z_]+)\(\)", r"|call:\1"),
            (r"==\s*(True|False)", r" is \1"),
            (r"!=\s*(True|False)", r" is not \1"),
            (r"==\s*([^%}\s]+)", r" == \1"),
            (r"{%\s*macro\s+([^%}]+)\s*%}", r"{% with \1 %}"),
            (r"{%\s*import\s+([^%}]+)\s*%}", r"{% include '\1' %}"),
            (r"{%\s*set\s+([^%}]+)\s*%}", r"{% with \1 %}"),
            (r"for\s+i\s+in\s+range\(([^)]+)\)", r"for i in range \1")
        ]

    def convert(self, template_content: str = None) -> str:
        """Convert template content from Jinja2 to Django template syntax."""
        # If no content provided, read from file
        if template_content is None:
            try:
                with open(self.template_path, 'r', encoding='utf-8') as f:
                    template_content = f.read()
            except Exception as e:
                raise ValueError(f"Could not read template file: {str(e)}")

        if not template_content:
            return ""
            
        content = template_content
        
        # Apply conversion patterns
        for pattern_name, (pattern, replacement) in self.conversion_patterns.items():
            content = re.sub(pattern, replacement, content)
        
        # Apply fixes
        for pattern, replacement in self.fixes:
            content = re.sub(pattern, replacement, content)
        
        # Convert blocks
        content = self._convert_blocks(content)
        
        # Convert control structures
        content = self._convert_control_structures(content)
        
        # Convert static tags
        content = self._convert_static_tags(content)
        
        # Write the converted content to output directory
        try:
            # Create relative path to maintain directory structure
            rel_path = self.template_path.relative_to(self.template_path.parent.parent)
            output_path = self.output_dir / rel_path
            
            # Create output directory if it doesn't exist
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Write converted content
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(content)
        except Exception as e:
            raise ValueError(f"Could not write converted template: {str(e)}")

        return content

    def process_template(self, template_path: str) -> None:
        """Process a single template file."""
        try:
            # Convert string path to Path object
            template_path = Path(template_path)
            
            # Read template content
            with open(template_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Convert template
            converted_content = self.convert(content)
            
            # Create output path
            rel_path = template_path.relative_to(self.template_path)
            output_path = self.output_dir / rel_path
            
            # Create output directory if it doesn't exist
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Write converted content
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(converted_content)
                
        except Exception as e:
            print(f"Error processing {template_path}: {str(e)}")

    def _convert_blocks(self, content: str) -> str:
        """Convert Jinja2 block syntax to Django template syntax"""
        # Convert block definitions
        content = re.sub(
            r'{%\s*block\s+([^%}]+)\s*%}',
            r'{% block \1 %}',
            content
        )

        # Convert endblock tags
        content = re.sub(
            r'{%\s*endblock\s*(?:([^%}]+))?\s*%}',
            lambda m: f"{{% endblock {m.group(1) or ''} %}}", 
            content
        )

        return content

    def _convert_control_structures(self, content: str) -> str:
        """Convert Jinja2 control structures to Django syntax"""
        # Convert if statements
        content = re.sub(
            r'{%\s*if\s+(.+?)\s*%}',
            lambda m: f"{{% if {self._convert_conditions(m.group(1))} %}}",
            content
        )

        # Convert for loops
        content = re.sub(
            r'{%\s*for\s+(.+?)\s+in\s+(.+?)\s*%}',
            r'{% for \1 in \2 %}',
            content
        )

        # Convert else statements
        content = re.sub(
            r'{%\s*else\s*%}',
            r'{% else %}',
            content
        )

        return content

    def _convert_static_tags(self, content: str) -> str:
        """Convert Jinja2 static file references to Django syntax"""
        # Convert static function calls
        content = re.sub(
            r'{{\s*static\([\'"]([^\'"]+)[\'"]\)\s*}}',
            r"{% static '\1' %}",
            content
        )

        # Convert url_for with static files
        content = re.sub(
            r'{{\s*url_for\([\'"]static[\'"]\s*,\s*filename=[\'"]([^\'"]+)[\'"]\)\s*}}',
            r"{% static '\1' %}",
            content
        )

        return content

    def _convert_conditions(self, condition: str) -> str:
        """Convert Jinja2 condition syntax to Django syntax"""
        # Convert common operators
        condition = re.sub(r'\bis\s+not\b', 'is not', condition)
        condition = re.sub(r'\bis\b', '==', condition)
        condition = re.sub(r'\bnot\s+in\b', 'not in', condition)
        
        # Convert None comparisons
        condition = re.sub(r'\bNone\b', 'None', condition)
        
        # Convert boolean operators
        condition = re.sub(r'\band\b', 'and', condition)
        condition = re.sub(r'\bor\b', 'or', condition)
        condition = re.sub(r'\bnot\b', 'not', condition)
        
        # Convert method calls
        condition = re.sub(r'\.([a-zA-Z_]+)\(\)', r'.\1', condition)
        
        return condition

    def _convert_macro_syntax(self, content: str) -> str:
        """Convert Jinja2 macro syntax to Django template tags"""
        # Convert macro definitions to template includes
        content = re.sub(
            r'{%\s*macro\s+([^%}]+)\s*%}',
            r'{% include "\1" %}',
            content
        )

        # Convert macro calls
        content = re.sub(
            r'{{\s*([^}]+)\s*\(\s*([^}]*)\s*\)\s*}}',
            lambda m: self._convert_macro_call(m.group(1), m.group(2)),
            content
        )

        return content

    def _convert_macro_call(self, macro_name: str, args: str) -> str:
        """Convert a Jinja2 macro call to Django template syntax"""
        if not args:
            return f"{{% include '{macro_name}' %}}"
        
        # Convert positional and keyword arguments
        kwargs = []
        for arg in args.split(','):
            if '=' in arg:
                key, value = arg.split('=', 1)
                kwargs.append(f"{key.strip()}={value.strip()}")
            else:
                kwargs.append(arg.strip())
                
        return f"{{% include '{macro_name}' with {' '.join(kwargs)} %}}"