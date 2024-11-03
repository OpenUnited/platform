import os
import re

def update_migration_file(file_path):
    with open(file_path, 'r') as file:
        content = file.read()

    # Pattern matches 'apps.someappname' but not 'apps.capabilities' or 'apps.common'
    pattern = r'apps\.(?!capabilities|common|flows|portal|engagement|canopy)([\w_]+)'
    
    # Replace with 'apps.capabilities.\1'
    updated_content = re.sub(pattern, r'apps.capabilities.\1', content)
    
    # Only write if changes were made
    if content != updated_content:
        print(f"Updating {file_path}")
        with open(file_path, 'w') as file:
            file.write(updated_content)

def process_migrations():
    # Start from the current directory
    base_dir = '.'
    
    # Walk through all directories
    for root, dirs, files in os.walk(base_dir):
        # Skip virtual environment directories
        if 'env' in root or 'venv' in root or '.git' in root:
            continue
            
        # Process only migration files
        for file in files:
            if file.endswith('.py') and not file.startswith('__'):
                if 'migrations' in root:
                    file_path = os.path.join(root, file)
                    update_migration_file(file_path)

if __name__ == '__main__':
    print("Starting migration file updates...")
    process_migrations()
    print("Finished updating migration files.")
