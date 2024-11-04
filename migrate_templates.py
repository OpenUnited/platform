import os
import shutil
from pathlib import Path
from typing import Dict, List
import argparse

class TemplateMigrator:
    def __init__(self, source_dir: Path, dest_dir: Path, dry_run: bool = False):
        self.source_dir = source_dir
        self.dest_dir = dest_dir
        self.dry_run = dry_run
        self.changes: Dict[str, List[str]] = {
            'copy': [],
            'backup': []
        }

    def backup_templates(self) -> None:
        if self.dest_dir.exists():
            backup_dir = self.dest_dir.parent / f"{self.dest_dir.name}_backup"
            if not self.dry_run:
                shutil.copytree(self.dest_dir, backup_dir, dirs_exist_ok=True)
            self.changes['backup'].append(f"Backed up {self.dest_dir} to {backup_dir}")

    def copy_templates(self) -> None:
        for root, _, files in os.walk(self.source_dir):
            rel_path = Path(root).relative_to(self.source_dir)
            dest_path = self.dest_dir / rel_path
            
            for file in files:
                if file.endswith('.html'):
                    src_file = Path(root) / file
                    dest_file = dest_path / file
                    
                    if not self.dry_run:
                        os.makedirs(dest_path, exist_ok=True)
                        shutil.copy2(src_file, dest_file)
                    
                    self.changes['copy'].append(f"Copy {src_file} -> {dest_file}")

    def migrate(self) -> Dict[str, List[str]]:
        """Execute the migration and return a list of changes"""
        if not self.source_dir.exists():
            raise FileNotFoundError(f"Source directory {self.source_dir} does not exist")

        self.backup_templates()
        self.copy_templates()
        return self.changes

def main():
    parser = argparse.ArgumentParser(description='Migrate Django templates')
    parser.add_argument('--dry-run', action='store_true', 
                      help='Show what would be done without making changes')
    args = parser.parse_args()

    # Get the project root directory
    project_root = Path(__file__).parent
    source_dir = project_root / 'converted_templates'
    dest_dir = project_root / 'apps' / 'templates'

    try:
        migrator = TemplateMigrator(source_dir, dest_dir, dry_run=args.dry_run)
        changes = migrator.migrate()

        # Print summary of changes
        print("\nTemplate Migration Summary:")
        print("=" * 50)
        
        if changes['backup']:
            print("\nBackups:")
            for change in changes['backup']:
                print(f"  • {change}")

        if changes['copy']:
            print("\nFiles to be copied:")
            for change in changes['copy']:
                print(f"  • {change}")

        if args.dry_run:
            print("\nDRY RUN: No changes were made")
        else:
            print("\nMigration completed successfully!")

    except Exception as e:
        print(f"Error: {e}")
        return 1

    return 0

if __name__ == "__main__":
    exit(main())