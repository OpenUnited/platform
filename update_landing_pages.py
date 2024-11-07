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

def copy_files(source_dir, html_dest_dir, assets_dest_dir):
    """Copy HTML and asset files to their respective destinations"""
    # Ensure destination directories exist
    os.makedirs(html_dest_dir, exist_ok=True)
    os.makedirs(os.path.dirname(assets_dest_dir), exist_ok=True)
    
    # Copy HTML files
    for html_file in Path(source_dir).glob('*.html'):
        shutil.copy2(html_file, html_dest_dir)
        print(f"Copied {html_file.name} to {html_dest_dir}")
    
    # Copy assets
    assets_source = os.path.join(source_dir, 'assets')
    if os.path.exists(assets_dest_dir):
        print(f"Removing existing assets directory: {assets_dest_dir}")
        shutil.rmtree(assets_dest_dir)
    
    # Copy and list all copied assets
    shutil.copytree(assets_source, assets_dest_dir)
    copied_assets = list(Path(assets_dest_dir).glob('*'))
    print(f"\nReplaced assets directory with {len(copied_assets)} new files:")
    for asset in copied_assets:
        print(f"  - {asset.name}")

def update_asset_paths(html_content):
    """Update asset paths in HTML content"""
    # Fix any malformed quotes in the HTML first
    html_content = re.sub(r'(src|href)=([^"\s>]+)(?=[>\s])', r'\1="\2"', html_content)
    
    # Pattern to match both /landing-pages/assets/ and /static/landing-pages/assets/
    patterns = [
        # Match /landing-pages/assets/
        r'(src|href)=[\'"]*\/landing-pages\/assets\/([^"\'>]+)[\'"]*',
        # Match /static/landing-pages/assets/
        r'(src|href)=[\'"]*\/static\/landing-pages\/assets\/([^"\'>]+)[\'"]*',
        # Match paths without assets directory
        r'(src|href)=[\'"]*\/static\/landing-pages\/([^"\'>]+)[\'"]*',
        r'(src|href)=[\'"]*\/landing-pages\/([^"\'>]+)[\'"]*'
    ]
    
    # Fixed: Use double quotes for the static tag
    replacement = r'\1="{% static "landing-pages/assets/\2" %}"'
    replacement_no_assets = r'\1="{% static "landing-pages/\2" %}"'
    
    # Apply all replacements
    for i, pattern in enumerate(patterns):
        if i < 2:  # First two patterns use the assets directory
            html_content = re.sub(pattern, replacement, html_content)
        else:  # Last two patterns don't include assets directory
            html_content = re.sub(pattern, replacement_no_assets, html_content)
    
    return html_content

def process_html_files(directory):
    """Process HTML files to update asset paths"""
    html_files = Path(directory).glob('*.html')
    
    for html_file in html_files:
        try:
            # Read the file content
            with open(html_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Check if {% load static %} is present
            if '{% load static %}' not in content:
                # Add it after the DOCTYPE if it exists
                if '<!DOCTYPE' in content.upper() or '<!doctype' in content:
                    content = re.sub(r'(<!DOCTYPE[^>]*>|<!doctype[^>]*>)', r'\1\n{% load static %}', content, flags=re.IGNORECASE)
                else:
                    content = '{% load static %}\n' + content
            
            # Update the asset paths
            updated_content = update_asset_paths(content)
            
            # Write back only if changes were made
            if content != updated_content:
                with open(html_file, 'w', encoding='utf-8') as f:
                    f.write(updated_content)
                print(f"Updated: {html_file}")
            else:
                print(f"No changes needed: {html_file}")
                
        except Exception as e:
            print(f"Error processing {html_file}: {str(e)}")

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