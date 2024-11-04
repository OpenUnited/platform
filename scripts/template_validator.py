from django.template import Engine, Template, TemplateSyntaxError
from django.template.base import Token, TokenType
from pathlib import Path
from typing import Dict, List, Set, Tuple
import re

class TemplateValidator:
    def __init__(self):
        self.standalone_tags = {
            'load', 'csrf_token', 'spaceless', 'url', 'static', 'trans',
            'blocktrans', 'blocktranslate', 'autoescape', 'cycle'
        }
        
        self.closing_patterns = {
            'if': 'endif',
            'for': 'endfor',
            'block': 'endblock',
            'blocktrans': ['endblocktrans', 'endblocktranslate'],
            'blocktranslate': ['endblocktranslate', 'endblocktrans']
        }

    def validate(self, template_path: Path) -> Tuple[bool, str]:
        """Main validation entry point"""
        try:
            content = template_path.read_text()
            
            # Basic syntax check
            Template(content)
            
            # Validate tag structure
            self._validate_tag_structure(content)
            
            # Validate template inheritance
            self._validate_inheritance(template_path)
            
            return True, ''
            
        except TemplateSyntaxError as e:
            return False, str(e)
        except Exception as e:
            return False, f"Validation error: {str(e)}"

    def _validate_tag_structure(self, content: str) -> None:
        """Validate template tag structure and nesting"""
        stack = []
        
        for match in re.finditer(r'{%\s*(.+?)\s*%}', content):
            tag = match.group(1).split()[0]
            
            if tag in self.standalone_tags:
                continue
                
            if tag.startswith('end'):
                if not stack:
                    raise TemplateSyntaxError(f"Unexpected closing tag: {tag}")
                    
                opening_tag = stack.pop()
                expected_closing = self.closing_patterns.get(opening_tag)
                
                if isinstance(expected_closing, list):
                    if tag not in expected_closing:
                        raise TemplateSyntaxError(
                            f"Mismatched tags: expected {' or '.join(expected_closing)}, found {tag}"
                        )
                elif tag != expected_closing:
                    raise TemplateSyntaxError(
                        f"Mismatched tags: expected {expected_closing}, found {tag}"
                    )
            else:
                stack.append(tag)
                
        if stack:
            raise TemplateSyntaxError(f"Unclosed tags: {', '.join(stack)}")

    def _validate_inheritance(self, template_path: Path) -> bool:
        """Validate template inheritance structure"""
        try:
            content = template_path.read_text()
            
            # Check extends tag
            extends_tags = re.findall(r'{%\s*extends\s+[\'"]([^\'"]+)[\'"]\s*%}', content)
            if extends_tags:
                parent_template = extends_tags[0]
                # Verify parent template exists
                for template_dir in self.template_dirs:
                    parent_path = template_dir / parent_template
                    if parent_path.exists():
                        return True
                return False
                
            return True
            
        except Exception:
            return False