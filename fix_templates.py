import os
import re

def fix_template_tags(directory):
    # Patterns to find static/url usage and load statements
    static_usage = re.compile(r'{%\s*static|{{\s*static')
    static_load = re.compile(r'{%\s*load\s+static\s*%}')
    extends_pattern = re.compile(r'{%\s*extends\s+[\'"]([^\'"]+)[\'"]\s*%}')
    
    files_modified = 0
    tags_added = 0
    
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith('.html'):
                filepath = os.path.join(root, file)
                
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Check if file uses static tag
                uses_static = bool(static_usage.search(content))
                has_load_static = bool(static_load.search(content))
                extends_match = extends_pattern.search(content)
                
                # Add load static if needed
                if uses_static and not has_load_static:
                    # If template extends another template, add after extends
                    if extends_match:
                        content = content.replace(
                            extends_match.group(0),
                            f"{extends_match.group(0)}\n{{% load static %}}"
                        )
                    else:
                        # Add to top of file
                        content = "{% load static %}\n" + content
                    
                    with open(filepath, 'w', encoding='utf-8') as f:
                        f.write(content)
                    
                    print(f"Added {{% load static %}} to {filepath}")
                    files_modified += 1
                    tags_added += 1
    
    print(f"\nSummary:")
    print(f"Files modified: {files_modified}")
    print(f"Load tags added: {tags_added}")

if __name__ == "__main__":
    directory = "apps/templates"  # Adjust this path to your templates directory
    print("Starting template fixes...")
    fix_template_tags(directory)
    print("Done!")