import os
import shutil
from pathlib import Path
import filecmp
import django
from datetime import datetime

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'apps.common.settings.development')
django.setup()

def migrate_templates():
    # Define paths
    source_dir = Path('apps/templates/product_management')
    target_dir = Path('apps/capabilities/product_management/templates/product_management')
    backup_dir = Path(f'template_backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}')

    if not source_dir.exists():
        print(f"Source directory {source_dir} does not exist!")
        return

    # Create backup directory
    backup_dir.mkdir(exist_ok=True)
    
    # Create target directory if it doesn't exist
    target_dir.mkdir(parents=True, exist_ok=True)

    moved_files = []
    skipped_files = []
    errors = []

    # First, create a backup of both directories
    print("\nCreating backups...")
    if source_dir.exists():
        shutil.copytree(source_dir, backup_dir / 'source_templates')
    if target_dir.exists():
        shutil.copytree(target_dir, backup_dir / 'target_templates')

    # Process each file in source directory
    print("\nMigrating templates...")
    for source_file in source_dir.rglob('*'):
        if source_file.is_file():
            # Calculate relative path
            rel_path = source_file.relative_to(source_dir)
            target_file = target_dir / rel_path
            
            try:
                # Create target subdirectories if needed
                target_file.parent.mkdir(parents=True, exist_ok=True)
                
                # Check if target file exists and is different
                if target_file.exists():
                    if filecmp.cmp(source_file, target_file, shallow=False):
                        print(f"Skipping identical file: {rel_path}")
                        skipped_files.append(str(rel_path))
                        continue
                    else:
                        print(f"Updating different file: {rel_path}")
                else:
                    print(f"Copying new file: {rel_path}")
                
                # Copy file to new location
                shutil.copy2(source_file, target_file)
                moved_files.append(str(rel_path))
                
                # Delete source file
                source_file.unlink()
                
            except Exception as e:
                error_msg = f"Error processing {rel_path}: {str(e)}"
                print(f"ERROR: {error_msg}")
                errors.append(error_msg)

    # Remove empty directories in source
    try:
        if source_dir.exists():
            for dir_path in sorted([p for p in source_dir.rglob('*') if p.is_dir()], reverse=True):
                if not any(dir_path.iterdir()):
                    dir_path.rmdir()
            if not any(source_dir.iterdir()):
                source_dir.rmdir()
    except Exception as e:
        print(f"Error cleaning up directories: {str(e)}")

    # Write report
    report = {
        'timestamp': datetime.now().isoformat(),
        'source_dir': str(source_dir),
        'target_dir': str(target_dir),
        'backup_dir': str(backup_dir),
        'moved_files': moved_files,
        'skipped_files': skipped_files,
        'errors': errors
    }

    with open(backup_dir / 'migration_report.txt', 'w') as f:
        f.write("Template Migration Report\n")
        f.write("======================\n\n")
        f.write(f"Timestamp: {report['timestamp']}\n")
        f.write(f"Source: {report['source_dir']}\n")
        f.write(f"Target: {report['target_dir']}\n")
        f.write(f"Backup: {report['backup_dir']}\n\n")
        
        f.write(f"Moved Files ({len(moved_files)}):\n")
        for file in moved_files:
            f.write(f"  - {file}\n")
        
        f.write(f"\nSkipped Files ({len(skipped_files)}):\n")
        for file in skipped_files:
            f.write(f"  - {file}\n")
        
        f.write(f"\nErrors ({len(errors)}):\n")
        for error in errors:
            f.write(f"  - {error}\n")

    # Print summary
    print("\nMigration Complete!")
    print(f"Moved: {len(moved_files)} files")
    print(f"Skipped: {len(skipped_files)} files")
    print(f"Errors: {len(errors)} files")
    print(f"\nBackup created at: {backup_dir}")
    print("See migration_report.txt in backup directory for details")

    if errors:
        print("\nWARNING: Some errors occurred during migration!")
        print("Please check the migration report for details.")

if __name__ == '__main__':
    # Ask for confirmation
    print("This script will:")
    print("1. Copy templates from apps/templates/product_management/")
    print("   to apps/capabilities/product_management/templates/product_management/")
    print("2. Create a backup of both directories")
    print("3. Delete the original templates from apps/templates/product_management/")
    
    confirm = input("\nDo you want to continue? (y/n): ")
    
    if confirm.lower() == 'y':
        migrate_templates()
    else:
        print("Migration cancelled.")
