import os
from pathlib import Path
from collections import defaultdict
import shutil
from datetime import datetime

def get_template_mappings():
    return {
        # App-specific templates
        'security': 'capabilities/security',
        'talent': 'capabilities/talent',
        'portal': 'portal',
        
        # Product Management templates
        'product_management': {
            'patterns': [
                'product_detail.html',
                'product_tree/*',
                'products/*',
                'product_area_detail/*',
                'product_area_detail_helper/*',
                'unauthenticated_tree/*'
            ],
            'target': 'capabilities/product_management'
        },
        
        # Shared components and layouts
        'common': {
            'patterns': [
                'base.html',
                'footer.html',
                'header.html',
                'navbar.html',
                '404.html',
                'about.html',
                'home.html',
                'privacy_policy.html',
                'terms_of_use.html',
                'toast.html',
                'logo.html',
                'main.html',
                'base_html.html',
                'header_full.html',
                'header_without_discord.html',
                'video_player_modal.html',
                'complete_profile_pop_up.html',
                'selectable_dropdown.html'
            ],
            'target': 'common'
        },
        
        # Forms
        'forms': {
            'patterns': [
                'forms/*',
                'attachments.html'
            ],
            'target': 'common/forms'
        },
        
        # Components that should be moved to a shared components app
        'components': {
            'patterns': [
                'components/*',
                'partials/*',
                'macros/*',
                'helper/*',
                'filters/*',
                'buttons/*',
                'bounty/*',
                'bounties/*',
                'challenges/*',
                'agreements/*',
                'work/*',
                'users/*',
                'sub_header/*',
                'header/*'
            ],
            'target': 'common/components'
        }
    }

def organize_templates():
    source_dir = Path('apps/templates')
    backup_dir = Path(f'template_backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}')
    
    print("Starting template organization...")
    
    # Create backup
    print("\nCreating backup...")
    shutil.copytree(source_dir, backup_dir / 'templates')
    
    mappings = get_template_mappings()
    moved_files = defaultdict(list)
    skipped_files = []
    
    # Process each file
    for template_path in source_dir.rglob('*.html'):
        relative_path = template_path.relative_to(source_dir)
        first_dir = str(relative_path).split('/')[0]
        matched = False
        
        # Check direct app mappings
        if first_dir in ['security', 'talent', 'portal']:
            target_app = mappings[first_dir]
            target_path = Path(f'apps/{target_app}/templates/{relative_path}')
            matched = True
        else:
            # Check pattern-based mappings
            for app, config in mappings.items():
                if isinstance(config, dict) and 'patterns' in config:
                    for pattern in config['patterns']:
                        if pattern.endswith('/*'):
                            if str(relative_path).startswith(pattern[:-2]):
                                target_app = config['target']
                                target_path = Path(f'apps/{target_app}/templates/{relative_path}')
                                matched = True
                                break
                        elif str(relative_path) == pattern:
                            target_app = config['target']
                            target_path = Path(f'apps/{target_app}/templates/{relative_path}')
                            matched = True
                            break
                    if matched:
                        break
        
        if matched:
            print(f"Moving {relative_path} to {target_path}")
            target_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(template_path, target_path)
            moved_files[target_app].append(str(relative_path))
            # Delete the original file after successful copy
            template_path.unlink()
        else:
            print(f"Skipping {relative_path} - no mapping found")
            skipped_files.append(str(relative_path))
    
    # Clean up empty directories
    for path in sorted([p for p in source_dir.rglob('*') if p.is_dir()], reverse=True):
        if path.exists() and not any(path.iterdir()):
            path.rmdir()
    
    # Write report
    with open(backup_dir / 'migration_report.txt', 'w') as f:
        f.write("Template Migration Report\n")
        f.write("======================\n\n")
        
        for app, files in moved_files.items():
            f.write(f"\n{app}:\n")
            f.write(f"Moved {len(files)} files:\n")
            for file in sorted(files):
                f.write(f"  - {file}\n")
        
        f.write("\nSkipped files:\n")
        for file in sorted(skipped_files):
            f.write(f"  - {file}\n")
    
    print("\nMigration complete!")
    print(f"Backup created at: {backup_dir}")
    print("See migration_report.txt for details")
    
    if skipped_files:
        print("\nSkipped files that can be deleted:")
        for file in sorted(skipped_files):
            print(f"  - {file}")
        
        if input("\nDelete skipped files? (y/n): ").lower() == 'y':
            for file in skipped_files:
                file_path = source_dir / file
                if file_path.exists():
                    file_path.unlink()
                    print(f"Deleted: {file}")

if __name__ == '__main__':
    print("This script will organize templates into their respective apps.")
    print("A backup will be created before any changes are made.")
    confirm = input("\nProceed? (y/n): ")
    
    if confirm.lower() == 'y':
        organize_templates()
    else:
        print("Operation cancelled.")