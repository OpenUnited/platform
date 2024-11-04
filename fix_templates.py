import os
import re

def fix_template_tags(directory):
    # Patterns to find unquoted tags
    static_no_quotes = re.compile(r'{%\s*static\s+([^\'"\s][^%\s]+)\s*%}')
    url_no_quotes = re.compile(r'{%\s*url\s+([^\'"\s][^%\s]+)\s*%}')
    
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith('.html'):
                filepath = os.path.join(root, file)
                
                with open(filepath, 'r') as f:
                    content = f.read()
                
                # Add quotes to static paths that don't have them
                content = static_no_quotes.sub(lambda m: "{% static '" + m.group(1) + "' %}", content)
                
                # Add quotes to url names that don't have them
                content = url_no_quotes.sub(lambda m: "{% url '" + m.group(1) + "' %}", content)
                
                with open(filepath, 'w') as f:
                    f.write(content)
                
                print(f"Processed: {filepath}")

if __name__ == "__main__":
    directory = "."
    fix_template_tags(directory)