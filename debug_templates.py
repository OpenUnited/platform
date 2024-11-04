import os
from pathlib import Path

def debug_templates():
    print("Starting debug...")
    
    # 1. Print current directory
    print(f"\nCurrent working directory: {os.getcwd()}")
    
    # 2. Check templates directory
    templates_dir = Path('apps/templates')
    print(f"\nChecking templates directory: {templates_dir.absolute()}")
    print(f"Directory exists: {templates_dir.exists()}")
    
    # 3. Try to list files
    if templates_dir.exists():
        print("\nListing all .html files:")
        count = 0
        for file in templates_dir.rglob('*.html'):
            count += 1
            print(f"  - {file.relative_to(templates_dir)}")
        print(f"\nTotal files found: {count}")
    
    # 4. List direct contents of apps directory
    apps_dir = Path('apps')
    if apps_dir.exists():
        print("\nContents of apps directory:")
        for item in apps_dir.iterdir():
            print(f"  - {item.name}")
    else:
        print("\napps directory not found!")

if __name__ == "__main__":
    try:
        debug_templates()
    except Exception as e:
        print(f"\nError occurred: {str(e)}")
        import traceback
        print("\nFull traceback:")
        traceback.print_exc() 