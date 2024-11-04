import os
import django
from django.template.loader import get_template
from django.template.loaders.app_directories import get_app_template_dirs

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'apps.common.settings.development')
django.setup()

def check_template_paths():
    # Get all template dirs
    from django.conf import settings
    template_dirs = []
    
    # Get dirs from settings
    for template_setting in settings.TEMPLATES:
        template_dirs.extend(template_setting.get('DIRS', []))
    
    # Get app template dirs
    app_template_dirs = get_app_template_dirs('templates')
    template_dirs.extend(app_template_dirs)
    
    print("Template search paths in order:")
    for i, dir in enumerate(template_dirs, 1):
        print(f"{i}. {dir}")
    
    # Check specific template
    template_name = "product_management/products.html"
    try:
        template = get_template(template_name)
        print(f"\nTemplate '{template_name}' is loaded from:")
        print(template.origin.name)
    except Exception as e:
        print(f"\nError loading template: {str(e)}")

if __name__ == '__main__':
    check_template_paths() 