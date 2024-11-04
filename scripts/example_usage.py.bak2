import sys
from pathlib import Path
import os
import django
from typing import List
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from template_analyzer import TemplateAnalyzer  # Custom dependency
from template_converter import StagedConverter  # Custom dependency
from template_validator import TemplateValidator  # Custom dependency

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

# Initialize Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'apps.common.settings.development')
django.setup()

console = Console()

def analyze_templates(templates: List[Path]) -> TemplateAnalyzer:
    """Analyze templates and build dependency graph"""
    analyzer = TemplateAnalyzer()
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        transient=True,
    ) as progress:
        task = progress.add_task("Analyzing templates...", total=len(templates))
        
        for template in templates:
            try:
                with open(template, 'r', encoding='utf-8') as f:
                    content = f.read()
                analyzer.analyze_template(str(template), content)
                progress.advance(task)
            except Exception as e:
                console.print(f"[red]Error analyzing {template}: {str(e)}[/red]")
    
    return analyzer

def is_excluded(path: Path) -> bool:
    """Check if path should be excluded"""
    excluded_patterns = [
        'env', 'venv', '.env', '.venv', 'node_modules', '__pycache__', '.git'
    ]
    # Check if any part of the path matches an excluded pattern
    return any(part in excluded_patterns for part in path.parts)

def find_template_dirs(start_path: Path) -> List[Path]:
    """Find all template directories, excluding virtual environments"""
    template_dirs = []
    
    for path in start_path.rglob('*'):
        # Skip excluded directories
        if is_excluded(path):
            continue
            
        # Look for template directories
        if path.is_dir() and path.name in ['templates', 'jinja2']:
            template_dirs.append(path)

    return template_dirs

def find_templates(template_dirs: List[Path]) -> List[Path]:
    """Find all template files in the given directories"""
    templates = []
    template_extensions = {'.html', '.htm', '.j2', '.jinja', '.jinja2'}
    
    for directory in template_dirs:
        for root, _, files in os.walk(directory):
            root_path = Path(root)
            
            # Skip if this is an excluded directory
            if is_excluded(root_path):
                continue
                
            # Process all template files in current directory
            for file in files:
                if any(file.endswith(ext) for ext in template_extensions):
                    template_path = root_path / file
                    templates.append(template_path)
    
    return templates

def find_html_files(start_path: Path) -> List[Path]:
    """Find all HTML files recursively, excluding dependency directories"""
    html_files = []
    
    # Common dependency and build directories to exclude
    excluded_patterns = {
        'env', 'venv', '.env', '.venv',
        'node_modules', '__pycache__', '.git',
        'dist', 'build', 'target', 'out'
    }
    
    for path in start_path.rglob('*.html'):
        # Skip excluded directories
        if any(part in excluded_patterns for part in path.parts):
            continue
            
        if path.is_file():
            html_files.append(path)
            
    return html_files

def convert_templates(html_files: List[Path], output_dir: Path) -> dict:
    """Convert Jinja2 templates to Django templates while preserving directory structure"""
    results = {
        'success': [], 
        'failed': [],
        'errors': {}
    }
    
    with Progress() as progress:
        task = progress.add_task("Converting templates...", total=len(html_files))
        
        for html_file in html_files:
            try:
                with open(html_file, 'r', encoding='utf-8') as f:
                    content = f.read()

                # Identify the base directory for relative path calculation
                base_dir = next((parent for parent in html_file.parents if parent.name in ['templates', 'jinja2']), project_root)
                
                # Get relative path from the base directory
                rel_path = html_file.relative_to(base_dir)

                # Create output path preserving directory structure
                out_file = output_dir / rel_path

                # Replace the file extension with .html (for Django templates)
                out_file = out_file.with_suffix('.html')

                # Create all parent directories
                out_file.parent.mkdir(parents=True, exist_ok=True)

                # Convert content from Jinja2 to Django template syntax
                converter = StagedConverter(
                    template_path=html_file,
                    output_dir=output_dir
                )
                converted_content = converter.convert(content)
                
                # Write converted content to file
                with open(out_file, 'w', encoding='utf-8') as f:
                    f.write(converted_content)
                    
                results['success'].append(html_file)
                
            except Exception as e:
                results['failed'].append(html_file)
                results['errors'][html_file.name] = str(e)
                console.print(f"[red]Error converting {html_file.name}: {str(e)}[/red]")
                
            progress.advance(task)
                
    return results

def main():
    """Main entry point"""
    html_files = find_html_files(project_root)
    console.print(f"\nFound {len(html_files)} HTML files to convert")
    
    output_dir = project_root / "converted_templates"
    results = convert_templates(html_files, output_dir)
    
    # Print results with error messages
    console.print("\nSuccessful conversions:")
    for html_file in results['success']:
        console.print(f"✓ {html_file.name}")
        
    console.print("\nFailed conversions:")
    for html_file in results['failed']:
        error_msg = results['errors'].get(html_file.name, 'Unknown error')
        console.print(f"✗ {html_file.name}: {error_msg}")

if __name__ == "__main__":
    main()
