#!/usr/bin/env python3
"""
Utility script to clean up empty directories in the CD ripping output folder.
Run this to clean up any empty artist directories left behind after reorganizations.
"""

from pathlib import Path
import sys

def cleanup_empty_directories(output_dir: Path):
    """Clean up empty artist directories"""
    print(f"Scanning for empty directories in: {output_dir}")
    
    empty_dirs = []
    
    # Check each artist directory
    for item in output_dir.iterdir():
        if item.is_dir():
            try:
                # Check if directory is empty
                if not any(item.iterdir()):
                    empty_dirs.append(item)
                else:
                    print(f"✅ {item.name} - contains albums")
            except PermissionError:
                print(f"❌ {item.name} - permission denied")
    
    if not empty_dirs:
        print("\n🎉 No empty directories found!")
        return
    
    print(f"\n📁 Found {len(empty_dirs)} empty directories:")
    for i, dir_path in enumerate(empty_dirs, 1):
        print(f"   {i}. {dir_path.name}")
    
    # Ask for confirmation
    confirm = input(f"\nRemove all {len(empty_dirs)} empty directories? (y/n): ").lower().strip()
    
    if confirm in ['y', 'yes']:
        removed = 0
        for dir_path in empty_dirs:
            try:
                dir_path.rmdir()
                print(f"✅ Removed: {dir_path.name}")
                removed += 1
            except OSError as e:
                print(f"❌ Failed to remove {dir_path.name}: {e}")
        
        print(f"\n🧹 Cleanup complete! Removed {removed}/{len(empty_dirs)} directories.")
    else:
        print("❌ Cleanup cancelled.")

def main():
    output_dir = Path.home() / "cd_ripping" / "output"
    
    if not output_dir.exists():
        print(f"❌ Output directory not found: {output_dir}")
        return 1
    
    cleanup_empty_directories(output_dir)
    return 0

if __name__ == "__main__":
    sys.exit(main())
