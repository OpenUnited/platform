import os
import shutil
import subprocess
import re
from pathlib import Path

def run_npm_build(landing_pages_dir):
    """Run npm build in the landing pages directory"""
    try:
        subprocess.run(['npm', 'run', 'build'], cwd=landing_pages_dir, check=True)
        print("Successfully built landing pages")
    except subprocess.CalledProcessError as e:
        print(f"Error building landing pages: {e}")
        raise

def copy_files(source_dir, html_dest_dir, static_root):
    """Copy HTML and asset files to their respective destinations"""
    # Ensure destination directories exist
    os.makedirs(html_dest_dir, exist_ok=True)
    assets_dest_dir = os.path.join(static_root, 'landing-pages', 'assets')
    
    # Copy HTML files
    for html_file in Path(source_dir).glob('*.html'):
        shutil.copy2(html_file, html_dest_dir)
        print(f"Copied {html_file.name} to {html_dest_dir}")
    
    # Copy assets
    assets_source = os.path.join(source_dir, 'assets')
    if os.path.exists(assets_dest_dir):
        print(f"Removing existing assets directory: {assets_dest_dir}")
        shutil.rmtree(assets_dest_dir)
    
    if os.path.exists(assets_source):
        # Use copy2 to preserve metadata and permissions
        shutil.copytree(assets_source, assets_dest_dir, copy_function=shutil.copy2)
        
        # Verify files were copied correctly
        copied_files = list(Path(assets_dest_dir).glob('*'))
        print(f"\nCopied {len(copied_files)} files to assets directory:")
        for file in copied_files:
            size = os.path.getsize(file)
            if size == 0:
                print(f"  WARNING: {file.name} is empty (0 bytes)")
            else:
                print(f"  - {file.name} ({size} bytes)")
    else:
        print(f"Warning: Assets source directory not found: {assets_source}")

def update_asset_paths(html_content):
    """Update asset paths in HTML content"""
    if html_content is None:
        return None
        
    # Add {% load static %} if not present
    if '{% load static %}' not in html_content:
        html_content = '{% load static %}\n' + html_content
    
    # Fix any malformed quotes in the HTML first
    html_content = re.sub(r'(src|href)=([^"\s>]+)(?=[>\s])', r'\1="\2"', html_content)
    
    # Replace static asset paths
    patterns = [
        r'(src|href)=[\'"]*/(?:static/)?(?:landing-pages/)?assets/([^"\']+)[\'"]',
    ]
    
    replacement = r'\1="{% static "assets/\2" %}"'
    
    for pattern in patterns:
        html_content = re.sub(pattern, replacement, html_content)
    
    # Replace navigation links
    nav_links = {
        # Logo and Home links
        r'href=[\'"]*(?:./)?index\.html[\'"]': r'href="{% url "marketing:index" %}"',
        r'<a href="index\.html"([^>]*)>': r'<a href="{% url "marketing:index" %}"\1>',
        r'<li class="font-medium"><a href="index\.html">Home</a></li>': r'<li class="font-medium"><a href="{% url "marketing:index" %}">Home</a></li>',
        
        # Auth buttons - replace onclick with href
        r'<a class="btn btn-ghost btn-sm" onclick="register_modal\.showModal\(\)">Sign in</a>': 
        r'<a class="btn btn-ghost btn-sm" href="{% url "security:sign_in" %}">Sign in</a>',
        
        r'<a class="btn btn-primary btn-sm" onclick="login_modal\.showModal\(\)">Sign up</a>': 
        r'<a class="btn btn-primary btn-sm" href="{% url "security:sign_up" %}">Sign up</a>',
        
        # Main navigation
        r'href=[\'"]*/(?:index\.html)?[\'"]': r'href="{% url "marketing:index" %}"',
        r'href=[\'"]*(?:./)?about\.html[\'"]': r'href="{% url "marketing:about" %}"',
        r'href=[\'"]*(?:./)?contact\.html[\'"]': r'href="{% url "marketing:contact" %}"',
        r'href=[\'"]*(?:./)?enterprise-support\.html[\'"]': r'href="{% url "marketing:enterprise_support" %}"',
        r'href=[\'"]*(?:./)?features\.html[\'"]': r'href="{% url "marketing:features" %}"',
        r'href=[\'"]*(?:./)?how-it-works\.html[\'"]': r'href="{% url "marketing:how_it_works" %}"',
        r'href=[\'"]*(?:./)?why-openunited\.html[\'"]': r'href="{% url "marketing:why_openunited" %}"',
        
        # Legal pages - updated to use terms.html
        r'href=[\'"]*(?:./)?privacy\.html[\'"]': r'href="{% url "marketing:privacy_policy" %}"',
        r'href=[\'"]*(?:./)?terms\.html[\'"]': r'href="{% url "marketing:terms" %}"',
        
        # Handle variations with /c/ prefix
        r'href=[\'"]*(?:./)?c/privacy-policy/?[\'"]': r'href="{% url "marketing:privacy_policy" %}"',
        r'href=[\'"]*(?:./)?c/terms/?[\'"]': r'href="{% url "marketing:terms" %}"',
        
        # Handle cross-references
        r'href=[\'"]*(?:./)?privacy(?:\.html)?[\'"]': r'href="{% url "marketing:privacy_policy" %}"',
        r'href=[\'"]*(?:./)?terms(?:\.html)?[\'"]': r'href="{% url "marketing:terms" %}"',
        
        # Authentication
        r'href=[\'"]*(?:./)?s/sign-in/?[\'"]': r'href="{% url "security:sign_in" %}"',
        r'href=[\'"]*(?:./)?s/sign-up/?[\'"]': r'href="{% url "security:sign_up" %}"',
        
        # Features sections
        r'href=[\'"]*(?:./)?features\.html#([^"\']+)[\'"]': r'href="{% url "marketing:features" %}#\1"',
        
        # Bounties
        r'href=[\'"]*(?:./)?bounties/?[\'"]': r'href="{% url "product_management:bounty-list" %}"',
        
        # Enterprise customers page
        r'href=[\'"]*(?:./)?enterprise-customers\.html[\'"]': r'href="{% url "marketing:enterprise_customers" %}"',
        r'href=[\'"]*(?:./)?c/enterprise-customers/?[\'"]': r'href="{% url "marketing:enterprise_customers" %}"',
    }
    
    for old_link, new_link in nav_links.items():
        html_content = re.sub(old_link, new_link, html_content)
    
    return html_content

def validate_html_links(html_content):
    """Validate that all links have been properly converted to Django template tags"""
    # Find all href attributes
    href_pattern = r'href=[\'"]([^\'"]+)[\'"]'
    links = re.findall(href_pattern, html_content)
    
    invalid_links = []
    
    for link in links:
        # Skip external links, anchors, and javascript
        if (link.startswith('http') or 
            link.startswith('#') or 
            link.startswith('javascript:') or 
            link.startswith('mailto:') or
            link == '#'):
            continue
            
        # Check if link is properly formatted as Django template tag
        if not (link.startswith('{% url') or link.startswith('{% static')):
            if link.endswith('.html'):
                invalid_links.append(f"HTML link not converted: {link}")
            elif '/assets/' in link:
                invalid_links.append(f"Static asset not converted: {link}")
            elif link.startswith('/'):
                invalid_links.append(f"Absolute path not converted: {link}")
    
    return invalid_links

def process_html_files(html_dir):
    """Process all HTML files in directory"""
    for html_file in Path(html_dir).glob('*.html'):
        try:
            print(f"Processing {html_file}...")
            
            # Read the file
            with open(html_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Update the content
            updated_content = update_asset_paths(content)
            
            if updated_content is None:
                raise ValueError(f"update_asset_paths returned None for {html_file}")
            
            # Validate the updated content
            invalid_links = validate_html_links(updated_content)
            if invalid_links:
                print(f"\nWarning: Found unconverted links in {html_file}:")
                for link in invalid_links:
                    print(f"  - {link}")
            
            # Write the updated content back
            with open(html_file, 'w', encoding='utf-8') as f:
                f.write(updated_content)
                
            print(f"Successfully updated {html_file}")
            
        except Exception as e:
            print(f"Error processing {html_file}: {e}")

def main():
    # Get the current script's directory (platform root)
    platform_root = Path(os.getcwd())
    
    # Define paths
    landing_pages_dir = platform_root.parent / 'landing-pages'
    docs_dir = landing_pages_dir / 'docs'
    html_dest_dir = platform_root / 'apps' / 'marketing' / 'templates' / 'landing-pages'
    assets_dest_dir = platform_root / 'apps' / 'marketing' / 'static' / 'assets'
    
    try:
        # Run npm build
        print("Building landing pages...")
        run_npm_build(landing_pages_dir)
        
        # Copy files
        print("\nCopying files...")
        copy_files(docs_dir, html_dest_dir, assets_dest_dir)
        
        # Update asset paths
        print("\nUpdating asset paths...")
        process_html_files(html_dest_dir)
        
        print("\nProcess completed successfully!")
        
    except Exception as e:
        print(f"\nError: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    import sys
    sys.exit(main())