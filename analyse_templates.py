import os
import hashlib
from collections import defaultdict
from django.conf import settings
from django.template.loaders.app_directories import get_app_template_dirs

def get_file_hash(filepath):
    """Generate hash of file contents to identify true duplicates."""
    with open(filepath, 'rb') as f:
        return hashlib.md5(f.read()).hexdigest()

def get_template_dirs():
    """Get Django template directories in order of precedence."""
    template_dirs = []
    
    # Get directories from settings.TEMPLATES
    for template_setting in settings.TEMPLATES:
        template_dirs.extend(template_setting.get('DIRS', []))
        
        # Add app template directories if APP_DIRS is True
        if template_setting.get('APP_DIRS', False):
            template_dirs.extend(get_app_template_dirs('templates'))
    
    return template_dirs

def analyze_templates():
    # Store templates by their content hash
    content_duplicates = defaultdict(list)
    # Store templates by their name
    name_duplicates = defaultdict(list)
    
    template_dirs = get_template_dirs()
    
    # Walk through all template directories
    for root, _, files in os.walk("./apps"):
        for filename in files:
            if filename.endswith('.html'):
                filepath = os.path.join(root, filename)
                try:
                    content_hash = get_file_hash(filepath)
                    content_duplicates[content_hash].append(filepath)
                    name_duplicates[filename].append(filepath)
                except Exception as e:
                    print(f"Error processing {filepath}: {e}")

    print("=== Content-identical templates ===")
    for content_hash, paths in content_duplicates.items():
        if len(paths) > 1:
            print(f"\nIdentical content in {len(paths)} files:")
            # Sort paths by template directory precedence
            sorted_paths = sorted(paths, 
                key=lambda p: next((i for i, d in enumerate(template_dirs) 
                                  if p.startswith(str(d))), len(template_dirs)))
            
            for i, path in enumerate(sorted_paths):
                status = "USED" if i == 0 else "SHADOWED"
                print(f"- [{status}] {path}")

    print("\n=== Similarly named templates ===")
    for name, paths in name_duplicates.items():
        if len(paths) > 1:
            print(f"\n{name} appears in {len(paths)} locations:")
            # Check if contents are different
            hashes = {get_file_hash(p): p for p in paths}
            if len(hashes) > 1:
                print("(!) Different content in files with same name:")
                sorted_paths = sorted(paths, 
                    key=lambda p: next((i for i, d in enumerate(template_dirs) 
                                      if p.startswith(str(d))), len(template_dirs)))
                for i, path in enumerate(sorted_paths):
                    status = "USED" if i == 0 else "SHADOWED"
                    print(f"- [{status}] {path}")
            else:
                print("(Same content in all locations)")
                for path in paths:
                    print(f"- {path}")

if __name__ == "__main__":
    # Set up Django environment
    import django
    import sys
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "apps.common.settings.development")
    sys.path.extend([os.path.dirname(os.path.dirname(os.path.abspath(__file__)))])
    django.setup()
    
    analyze_templates()