import os
import csv
import django
from pathlib import Path

# Setup Django environment
def setup_django():
    # Assuming this script is in the root directory of your Django project
    # Adjust this path if needed
    project_root = Path(__file__).resolve().parent
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'apps.common.settings.development')
    
    # Add the project root to Python path
    import sys
    sys.path.append(str(project_root))
    
    django.setup()

def find_template_references(template_content):
    """Find extends and include statements in template content."""
    references = set()
    
    # Look for extends tags
    if '{% extends' in template_content:
        extends_start = template_content.find('{% extends')
        extends_end = template_content.find('%}', extends_start)
        if extends_start != -1 and extends_end != -1:
            extends_tag = template_content[extends_start:extends_end]
            # Look for template name in either single or double quotes
            try:
                if '"' in extends_tag:
                    template_name = extends_tag.split('"')[1]
                elif "'" in extends_tag:
                    template_name = extends_tag.split("'")[1]
                else:
                    template_name = extends_tag.split()[1].strip('"').strip("'")
                references.add(template_name)
            except (IndexError, ValueError):
                pass
    
    # Look for include tags
    start = 0
    while True:
        include_start = template_content.find('{% include', start)
        if include_start == -1:
            break
        
        include_end = template_content.find('%}', include_start)
        if include_end != -1:
            include_tag = template_content[include_start:include_end]
            try:
                if '"' in include_tag:
                    template_name = include_tag.split('"')[1]
                elif "'" in include_tag:
                    template_name = include_tag.split("'")[1]
                else:
                    template_name = include_tag.split()[1].strip('"').strip("'")
                references.add(template_name)
            except (IndexError, ValueError):
                pass
        start = include_end if include_end != -1 else len(template_content)
    
    # Also look for load tags that might load custom template tags
    start = 0
    while True:
        load_start = template_content.find('{% load', start)
        if load_start == -1:
            break
        
        load_end = template_content.find('%}', load_start)
        if load_end != -1:
            load_tag = template_content[load_start:load_end]
            try:
                # Add loaded template tags to references with a special prefix
                tags = load_tag.split()[1:]
                for tag in tags:
                    references.add(f"templatetag:{tag.strip()}")
            except (IndexError, ValueError):
                pass
        start = load_end if load_end != -1 else len(template_content)
    
    return references

def analyze_templates():
    """Analyze all templates in the project."""
    from django.conf import settings
    
    template_dirs = []
    
    # Get template directories from settings
    for template_setting in settings.TEMPLATES:
        template_dirs.extend(template_setting.get('DIRS', []))
        if template_setting.get('APP_DIRS', False):
            # Add template directories from installed apps
            for app_config in django.apps.apps.get_app_configs():
                template_dir = os.path.join(app_config.path, 'templates')
                if os.path.exists(template_dir):
                    template_dirs.append(template_dir)
    
    template_mapping = {}
    
    # Scan all template directories
    for template_dir in template_dirs:
        for root, _, files in os.walk(template_dir):
            for file in files:
                if file.endswith(('.html', '.htm', '.django')):
                    full_path = os.path.join(root, file)
                    relative_path = os.path.relpath(full_path, template_dir)
                    
                    try:
                        with open(full_path, 'r', encoding='utf-8') as f:
                            content = f.read()
                            references = find_template_references(content)
                            template_mapping[relative_path] = {
                                'path': full_path,
                                'references': references
                            }
                    except Exception as e:
                        print(f"Error processing {full_path}: {str(e)}")
    
    return template_mapping

def find_view_template_mappings():
    """Find which views use which templates."""
    from django.urls import get_resolver
    from django.urls.resolvers import URLPattern, URLResolver
    
    view_mappings = []
    
    def process_url_patterns(patterns, namespace=''):
        for pattern in patterns:
            if isinstance(pattern, URLResolver):
                process_url_patterns(pattern.url_patterns, pattern.namespace)
            elif isinstance(pattern, URLPattern):
                view = pattern.callback
                if hasattr(view, 'view_class'):
                    view = view.view_class
                
                template_name = None
                view_name = view.__name__ if hasattr(view, '__name__') else str(view)
                
                # Try to get template name from view
                if hasattr(view, 'template_name'):
                    template_name = view.template_name
                
                view_mappings.append({
                    'view_name': view_name,
                    'url_pattern': str(pattern.pattern),
                    'template_name': template_name
                })
    
    resolver = get_resolver()
    process_url_patterns(resolver.url_patterns)
    return view_mappings

def write_results_to_csv(template_mapping, view_mappings):
    """Write analysis results to CSV files."""
    # Write template dependencies
    with open('template_dependencies.csv', 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['Template', 'Dependencies'])
        for template, data in template_mapping.items():
            writer.writerow([template, ', '.join(data['references'])])
    
    # Write view-template mappings
    with open('view_template_mappings.csv', 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['View Name', 'URL Pattern', 'Template'])
        for mapping in view_mappings:
            writer.writerow([
                mapping['view_name'],
                mapping['url_pattern'],
                mapping['template_name'] or 'N/A'
            ])

def main():
    print("Setting up Django...")
    setup_django()
    
    print("Analyzing templates...")
    template_mapping = analyze_templates()
    
    print("Finding view-template mappings...")
    view_mappings = find_view_template_mappings()
    
    print("Writing results to CSV files...")
    write_results_to_csv(template_mapping, view_mappings)
    
    print("\nAnalysis complete! Results written to:")
    print("- template_dependencies.csv")
    print("- view_template_mappings.csv")

if __name__ == '__main__':
    main()