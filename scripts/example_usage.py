import sys
from pathlib import Path
import os
import django
from typing import List
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from template_analyzer import TemplateAnalyzer
from template_converter import TemplateConverter, StagedConverter
from template_validator import TemplateValidator

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

# Initialize Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'apps.common.settings.development')
django.setup()

console = Console()

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
                base_dir = next((parent for parent in html_file.parents 
                               if parent.name in ['templates', 'jinja2']), 
                              project_root)
                
                # Get relative path from the base directory
                rel_path = html_file.relative_to(base_dir)

                # Create output path preserving directory structure
                out_file = output_dir / rel_path
                out_file = out_file.with_suffix('.html')

                # Create all parent directories
                out_file.parent.mkdir(parents=True, exist_ok=True)

                # Use StagedConverter like in the original
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
    # Find all HTML files in the project
    html_files = find_html_files(project_root)
    console.print(f"\nFound {len(html_files)} HTML files to convert")
    
    # Set up output directory
    output_dir = project_root / "converted_templates"
    
    # Convert templates
    results = convert_templates(html_files, output_dir)
    
    # Print results
    console.print("\nConversion Results:")
    console.print(f"Successfully converted: {len(results['success'])} templates")
    console.print(f"Failed conversions: {len(results['failed'])} templates")
    
    if results['errors']:
        console.print("\n[bold red]Errors:[/bold red]")
        for template, error in results['errors'].items():
            console.print(f"{template}: {error}")

if __name__ == "__main__":
    main()
