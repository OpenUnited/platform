from pathlib import Path
from typing import Dict, Any, Tuple
from django.template import Template, Context, TemplateSyntaxError
from django.test import RequestFactory
from django.template.loader import get_template
import re

class TemplateTestSuite:
    def __init__(self, template_path: Path):
        self.template_path = template_path
        self.request_factory = RequestFactory()
        self.error_messages = {}
        
        # Common Django template tags that need to be loaded
        self.required_tag_libraries = [
            'static', 'i18n', 'l10n', 'cache', 'crispy_forms_tags',
            'admin_list', 'admin_modify', 'admin_urls', 'admin_tree',
            'admin_tree_list'
        ]
        
        # Add standalone tags from TemplateConverter
        self.standalone_tags = {
            'load', 'csrf_token', 'spaceless', 'url', 'static', 'trans',
            'blocktrans', 'blocktranslate', 'autoescape', 'cycle',
            'firstof', 'regroup', 'add_preserved_filters', 'paginator_number',
            'get_admin_log', 'endget_admin_log', 'admin_actions'
        }
        
        # Add special closing patterns from TemplateConverter
        self.special_closing_patterns = {
            'blocktrans': ['endblocktrans', 'endblocktranslate'],
            'blocktranslate': ['endblocktranslate', 'endblocktrans'],
            'plural': 'endplural',
            'spaceless': 'endspaceless',
            'autoescape': 'endautoescape',
            'regroup': 'endregroup',
            'firstof': 'endfirstof',
            'cycle': 'endcycle',
            'admin_actions': ['endadmin_actions', 'endblock']
        }
        
    def run_tests(self) -> Dict[str, bool]:
        """Run all template tests and store error messages"""
        results = {
            'syntax': self.test_syntax(),
            'django_tags': self.test_django_tags(),
            'url_patterns': self.test_url_patterns(),
            'static_patterns': self.test_static_patterns(),
            'block_syntax': self.test_block_syntax()
        }
        return results
    
    def get_errors(self) -> Dict[str, str]:
        """Get error messages for failed tests"""
        return self.error_messages
    
    def test_syntax(self) -> bool:
        """Test basic template syntax with improved tag loading"""
        try:
            content = self.template_path.read_text()
            
            # First validate template inheritance
            if not self._validate_inheritance(content):
                self.error_messages['syntax'] = "Invalid template inheritance structure"
                return False
                
            # Add all required template tags
            template_content = "{% load static %}\n"  # Start with static
            
            # Only add other tags if they're used in the template
            for lib in self.required_tag_libraries:
                if lib in content:
                    template_content += f"{{% load {lib} %}}\n"
            
            template_content += content
            
            # Enhanced context with common variables
            context = Context({
                'request': self.request_factory.get('/'),
                'user': None,
                'STATIC_URL': '/static/',
                'DEBUG': True,
                'page_obj': {'has_previous': lambda: False, 'has_next': lambda: False},
                'product': {'slug': 'test-slug'},
                'challenge': {'id': 1, 'product': {'slug': 'test-slug'}},
                'person': {'get_short_name': lambda: 'Test User'},
            })
            
            template = Template(template_content)
            template.render(context)
            return True
            
        except Exception as e:
            self.error_messages['syntax'] = f"Syntax error in template:\nError: {str(e)}"
            return False
    
    def test_django_tags(self) -> bool:
        """Test for proper Django template tag syntax"""
        content = self.template_path.read_text()
        
        # Common Django tag patterns
        patterns = [
            (r'{%\s*[^%}]+\s*%}', 'tag'),  # Basic tag syntax
            (r'{{\s*[^}]+\s*}}', 'variable'),   # Variable syntax
            (r'{#\s*[^#}]+\s*#}', 'comment')  # Comment syntax
        ]
        
        for pattern, tag_type in patterns:
            matches = re.findall(pattern, content)
            for match in matches:
                try:
                    test_content = "{% load static %}\n{% load i18n %}\n" + match
                    Template(test_content)
                except Exception as e:
                    self.error_messages['django_tags'] = f"Error in {tag_type}: {match}\n{str(e)}"
        return True
    
    def test_url_patterns(self) -> bool:
        """Test URL tag syntax"""
        content = self.template_path.read_text()
        url_patterns = re.findall(r'{%\s*url\s+[^%}]+\s*%}', content)
        
        for pattern in url_patterns:
            try:
                Template(pattern)
            except TemplateSyntaxError:
                return False
        return True
    
    def test_static_patterns(self) -> bool:
        """Test static file tag syntax"""
        content = self.template_path.read_text()
        static_patterns = re.findall(r'{%\s*static\s+[^%}]+\s*%}', content)
        
        for pattern in static_patterns:
            try:
                Template(f"{{% load static %}}\n{pattern}")
            except TemplateSyntaxError:
                return False
        return True
    
    def test_block_syntax(self) -> bool:
        """Test template inheritance block syntax"""
        content = self.template_path.read_text()
        
        try:
            # Check block tags are properly closed
            block_starts = re.findall(r'{%\s*block\s+(\w+)\s*%}', content)
            block_ends = re.findall(r'{%\s*endblock(?:\s+(\w+))?\s*%}', content)
            
            if len(block_starts) != len(block_ends):
                self.error_messages['block_syntax'] = "Mismatched number of block/endblock tags"
                return False
                
            # Check extends syntax
            extends_tags = re.findall(r'{%\s*extends\s+[^%}]+\s*%}', content)
            for tag in extends_tags:
                try:
                    Template(tag)
                except TemplateSyntaxError as e:
                    self.error_messages['block_syntax'] = f"Invalid extends syntax: {str(e)}"
                    return False
                    
            # Validate overall inheritance structure
            if not self._validate_inheritance(content):
                self.error_messages['block_syntax'] = "Invalid template inheritance structure"
                return False
                
            return True
            
        except Exception as e:
            self.error_messages['block_syntax'] = f"Block syntax error: {str(e)}"
            return False
    
    def get_test_context(self) -> Dict[str, Any]:
        """Generate a test context with common variables"""
        return {
            'request': self.request_factory.get('/'),
            'user': None,
            'csrf_token': 'dummy_token',
            # Add other common context variables as needed
        }
    
    def _validate_inheritance(self, content: str) -> bool:
        """Validate template inheritance and block structure"""
        try:
            tag_stack = []
            block_stack = []
            extends_found = False
            
            # Add required tag libraries
            template_content = "{% load static %}\n{% load i18n %}\n"
            
            # Parse and validate template
            try:
                Template(template_content + content)
            except TemplateSyntaxError:
                return False
                
            # Check tag structure
            for match in re.finditer(r'{%\s*(\w+)(?:\s+[^%}]*)?\s*%}', content):
                tag = match.group(1)
                
                if tag == 'extends':
                    if extends_found or tag_stack:  # extends must be first
                        return False
                    extends_found = True
                elif tag == 'block':
                    block_stack.append(tag)
                elif tag == 'endblock':
                    if not block_stack:
                        return False
                    block_stack.pop()
                elif tag not in self.standalone_tags:
                    if tag.startswith('end'):
                        if not tag_stack:
                            return False
                        start_tag = tag_stack[-1]
                        expected_close = self.special_closing_patterns.get(start_tag, f"end{start_tag}")
                        if isinstance(expected_close, list):
                            if tag not in expected_close:
                                return False
                        elif tag != expected_close:
                            return False
                        tag_stack.pop()
                    else:
                        tag_stack.append(tag)
                        
            return len(tag_stack) == 0 and len(block_stack) == 0
            
        except Exception:
            return False