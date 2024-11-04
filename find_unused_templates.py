import os
import django
from pathlib import Path
import re
from collections import defaultdict
import json

# Setup Django environment
def setup_django():
    project_root = Path(__file__).resolve().parent
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'apps.common.settings.development')
    import sys
    sys.path.append(str(project_root))
    django.setup()

def find_all_templates():
    """Find all template files in the project."""
    from django.conf import settings
    
    template_files = set()
    template_dirs = []
    
    # Get template directories from settings
    for template_setting in settings.TEMPLATES:
        template_dirs.extend(template_setting.get('DIRS', []))
        if template_setting.get('APP_DIRS', False):
            for app_config in django.apps.apps.get_app_configs():
                template_dir = os.path.join(app_config.path, 'templates')
                if os.path.exists(template_dir):
                    template_dirs.append(template_dir)
    
    # Find all template files
    for template_dir in template_dirs:
        for root, _, files in os.walk(template_dir):
            for file in files:
                if file.endswith(('.html', '.htm', '.django')):
                    full_path = os.path.join(root, file)
                    relative_path = os.path.relpath(full_path, template_dir)
                    template_files.add(relative_path)
    
    return template_files

def find_template_usage_in_code():
    """Find template references in Python files."""
    template_usage = set()
    python_files = []
    
    # Find all Python files
    for root, _, files in os.walk('.'):
        if 'env' in root or 'venv' in root or '.git' in root:
            continue
        for file in files:
            if file.endswith('.py'):
                python_files.append(os.path.join(root, file))
    
    # Patterns to search for
    patterns = [
        r'template_name\s*=\s*[\'"]([^\'"]+)[\'"]',
        r'template_name_suffix\s*=\s*[\'"]([^\'"]+)[\'"]',
        r'render\([^,]+,\s*[\'"]([^\'"]+)[\'"]',
        r'get_template\([\'"]([^\'"]+)[\'"]',
        r'select_template\(\[[^\]]+\]\)',
    ]
    
    for file_path in python_files:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                for pattern in patterns:
                    matches = re.finditer(pattern, content)
                    for match in matches:
                        if len(match.groups()) > 0:
                            template_usage.add(match.group(1))
        except Exception as e:
            print(f"Error processing {file_path}: {str(e)}")
    
    return template_usage

def find_template_usage_in_templates():
    """Find template references within templates."""
    template_usage = set()
    
    # Get template directories from settings
    from django.conf import settings
    template_dirs = []
    for template_setting in settings.TEMPLATES:
        template_dirs.extend(template_setting.get('DIRS', []))
        if template_setting.get('APP_DIRS', False):
            for app_config in django.apps.apps.get_app_configs():
                template_dir = os.path.join(app_config.path, 'templates')
                if os.path.exists(template_dir):
                    template_dirs.append(template_dir)
    
    # Find and process templates
    for template_dir in template_dirs:
        for root, _, files in os.walk(template_dir):
            for file in files:
                if file.endswith(('.html', '.htm', '.django')):
                    try:
                        full_path = os.path.join(root, file)
                        with open(full_path, 'r', encoding='utf-8') as f:
                            content = f.read()
                            # Look for extends tags
                            extends_matches = re.finditer(r'{%\s*extends\s*[\'"]([^\'"]+)[\'"]', content)
                            for match in extends_matches:
                                template_usage.add(match.group(1))
                            
                            # Look for include tags
                            include_matches = re.finditer(r'{%\s*include\s*[\'"]([^\'"]+)[\'"]', content)
                            for match in include_matches:
                                template_usage.add(match.group(1))
                    except Exception as e:
                        relative_path = os.path.relpath(full_path, template_dir)
                        print(f"Error processing template {relative_path}: {str(e)}")
    
    return template_usage

def find_dynamic_template_loading():
    """Find potential dynamic template loading patterns."""
    dynamic_patterns = defaultdict(list)
    
    for root, _, files in os.walk('.'):
        if 'env' in root or 'venv' in root or '.git' in root:
            continue
        for file in files:
            if file.endswith('.py'):
                file_path = os.path.join(root, file)
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        # Look for dynamic template loading patterns
                        patterns = [
                            r'get_template\(.*\+.*\)',
                            r'select_template\(.*\+.*\)',
                            r'render\([^,]+,\s*[^\'"][^,]+\)',
                            r'template_name\s*=\s*[^\'"][^,\n]+'
                        ]
                        for pattern in patterns:
                            matches = re.finditer(pattern, content)
                            for match in matches:
                                dynamic_patterns[file_path].append(match.group(0))
                except Exception as e:
                    print(f"Error checking dynamic loading in {file_path}: {str(e)}")
    
    return dynamic_patterns

def analyze_templates():
    """Main analysis function."""
    print("Setting up Django...")
    setup_django()
    
    print("\nFinding all templates...")
    all_templates = find_all_templates()
    
    print("\nFinding template usage in Python code...")
    code_usage = find_template_usage_in_code()
    
    print("\nFinding template usage in templates...")
    template_usage = find_template_usage_in_templates()
    
    print("\nChecking for dynamic template loading...")
    dynamic_loading = find_dynamic_template_loading()
    
    # Combine all usage
    used_templates = code_usage.union(template_usage)
    
    # Find potentially unused templates
    unused_templates = all_templates - used_templates
    
    # Write results
    results = {
        'all_templates': list(all_templates),
        'used_templates': list(used_templates),
        'unused_templates': list(unused_templates),
        'dynamic_loading_patterns': {k: v for k, v in dynamic_loading.items()}
    }
    
    with open('template_analysis.json', 'w') as f:
        json.dump(results, f, indent=2)
    
    print("\nAnalysis complete! Results written to template_analysis.json")
    print(f"\nFound {len(unused_templates)} potentially unused templates")
    print("\nWARNING: Please verify results before deleting any templates!")
    print("Special attention needed for files with dynamic template loading.")

if __name__ == '__main__':
    analyze_templates()