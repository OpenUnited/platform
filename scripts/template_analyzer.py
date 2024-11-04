from dataclasses import dataclass, field
from pathlib import Path
from typing import Set, Dict, List
import re

@dataclass
class TemplateNode:
    path: Path
    extends: Set[str] = field(default_factory=set)
    included_by: Set[str] = field(default_factory=set)
    includes: Set[str] = field(default_factory=set)
    complexity_score: int = 0
    
    def calculate_complexity(self, content: str) -> None:
        """Calculate template complexity score based on various factors"""
        patterns = {
            # Template inheritance
            r'{%\s*extends\s': 5,     # Template inheritance
            r'{%\s*include\s': 3,     # Template includes
            r'{%\s*block\s': 2,       # Block definitions
            
            # Control structures
            r'{%\s*if\s': 2,          # If statements
            r'{%\s*for\s': 2,         # For loops
            r'{%\s*with\s': 2,        # With blocks
            
            # Variables and filters
            r'{{.*?}}': 1,            # Variable output
            r'\|.*?}}': 1,            # Filter usage
            
            # Custom tags and complex operations
            r'{%\s*url\s': 2,         # URL generation
            r'{%\s*static\s': 1,      # Static file references
            r'{%\s*csrf_token\s': 1,  # CSRF token
            r'{%\s*load\s': 1,        # Loading template tags
        }
        
        self.complexity_score = 0
        for pattern, score in patterns.items():
            matches = re.findall(pattern, content)
            self.complexity_score += len(matches) * score

class TemplateAnalyzer:
    def __init__(self):
        self.nodes: Dict[str, TemplateNode] = {}
        self.base_templates: Set[str] = set()
        
    def analyze_template(self, path: Path, content: str) -> None:
        """Analyze a template file and update the dependency graph"""
        # Convert string path to Path object if needed
        path = Path(path) if isinstance(path, str) else path
        
        # Get template name relative to the first templates directory in its path
        template_parts = path.parts
        template_index = template_parts.index('templates') if 'templates' in template_parts else -1
        if template_index == -1:
            template_name = str(path)
        else:
            template_name = str(Path(*template_parts[template_index + 1:]))
        
        # Create or get node
        if template_name not in self.nodes:
            self.nodes[template_name] = TemplateNode(path=path)
        node = self.nodes[template_name]
        
        # Find extends
        extends_matches = re.findall(r'{%\s*extends\s+[\'"](.+?)[\'"]', content)
        for extended in extends_matches:
            node.extends.add(extended)
            if extended in self.nodes:
                self.nodes[extended].included_by.add(template_name)
        
        # Find includes
        include_matches = re.findall(r'{%\s*include\s+[\'"](.+?)[\'"]', content)
        for included in include_matches:
            node.includes.add(included)
            if included in self.nodes:
                self.nodes[included].included_by.add(template_name)
        
        # Calculate complexity
        node.calculate_complexity(content)
        
        # Update base templates set
        if not node.extends:
            self.base_templates.add(template_name)
        
    def get_conversion_order(self) -> List[str]:
        """Determine optimal order for template conversion"""
        ordered = []
        visited = set()
        
        def visit(template_name: str) -> None:
            """Visit a node and its dependencies"""
            if template_name in visited:
                return
                
            visited.add(template_name)
            node = self.nodes[template_name]
            
            # First convert extended templates
            for extended in node.extends:
                if extended in self.nodes:
                    visit(extended)
            
            # Then convert included templates
            for included in node.includes:
                if included in self.nodes:
                    visit(included)
            
            ordered.append(template_name)
        
        # Start with base templates
        for base in sorted(self.base_templates):
            visit(base)
        
        # Handle any remaining templates
        for template in sorted(self.nodes.keys()):
            visit(template)
        
        return ordered