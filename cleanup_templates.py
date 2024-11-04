from pathlib import Path

def cleanup_empty_directories():
    templates_dir = Path('apps/templates')
    
    print("Cleaning up empty directories...")
    
    # Get all directories in reverse order (deepest first)
    dirs = sorted([d for d in templates_dir.rglob('*') if d.is_dir()], reverse=True)
    
    for dir_path in dirs:
        try:
            if dir_path.exists() and not any(dir_path.iterdir()):
                print(f"Removing empty directory: {dir_path}")
                dir_path.rmdir()
        except Exception as e:
            print(f"Error removing {dir_path}: {e}")
    
    # Finally, try to remove the templates directory itself
    if templates_dir.exists() and not any(templates_dir.iterdir()):
        print(f"\nRemoving empty templates directory: {templates_dir}")
        templates_dir.rmdir()
    
    print("\nCleanup complete!")

if __name__ == "__main__":
    cleanup_empty_directories() 