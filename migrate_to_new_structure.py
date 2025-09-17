#!/usr/bin/env python3
"""
Migration Script - Transition to New Organized Structure

This script helps migrate from the old flat file structure to the new 
organized modular structure while preserving all existing functionality.

Usage:
    python3 migrate_to_new_structure.py [--backup] [--dry-run]

Options:
    --backup    Create backup of original files before moving
    --dry-run   Show what would be done without making changes
"""

import shutil
import sys
from pathlib import Path
import argparse

def main():
    parser = argparse.ArgumentParser(description="Migrate to new organized structure")
    parser.add_argument('--backup', action='store_true', help='Create backup before migration')
    parser.add_argument('--dry-run', action='store_true', help='Show changes without applying')
    args = parser.parse_args()
    
    base_dir = Path.cwd()
    
    # File mapping from old locations to new organized structure
    file_moves = {
        # Core functionality
        'rip_cd.py': 'src/core/rip_cd.py',
        'enrich_metadata.py': 'src/core/enrich_metadata.py',
        
        # Cover art management
        'discogs_cover_manager.py': 'src/cover_art/discogs_cover_manager.py',
        'batch_cover_processor.py': 'src/cover_art/batch_cover_processor.py',
        'manual_cover_manager.py': 'src/cover_art/manual_cover_manager.py',
        'manual_cover_updater.py': 'src/cover_art/manual_cover_updater.py',
        'simple_cover_manager.py': 'src/cover_art/simple_cover_manager.py',
        
        # Reports and analysis
        'cover_art_report.py': 'src/reports/cover_art_report.py',
        'find_missing_covers.py': 'src/reports/find_missing_covers.py',
        
        # Maintenance and migration
        'generate_rip_info.py': 'src/maintenance/generate_rip_info.py',
        'validate_cover_art.py': 'src/maintenance/validate_cover_art.py',
        'migrate_artist.py': 'src/maintenance/migrate_artist.py',
        'migrate_compilations.py': 'src/maintenance/migrate_compilations.py',
        'cleanup_empty_dirs.py': 'src/maintenance/cleanup_empty_dirs.py',
        
        # Specialized tools
        'single_metadata_updater.py': 'src/tools/single_metadata_updater.py',
        'test_artist_choice.py': 'src/tools/test_artist_choice.py',
    }
    
    print("🔄 CD Manager Structure Migration")
    print("=" * 50)
    
    if args.backup:
        backup_dir = base_dir / 'backup_old_structure'
        backup_dir.mkdir(exist_ok=True)
        print(f"📦 Creating backup in {backup_dir}")
    
    # Check current state
    if (base_dir / 'src').exists() and list((base_dir / 'src').rglob('*.py')):
        print("✅ New structure already exists!")
        print("📁 Files already organized in src/ directory")
        
        # Check if old files still exist
        old_files = [f for f in file_moves.keys() if (base_dir / f).exists()]
        if old_files:
            print(f"\n⚠️  Found {len(old_files)} files in old locations:")
            for old_file in old_files:
                print(f"   • {old_file}")
            
            if not args.dry_run:
                response = input("\nMove these to archive folder? (y/N): ")
                if response.lower() == 'y':
                    archive_dir = base_dir / 'old_files_archive'
                    archive_dir.mkdir(exist_ok=True)
                    for old_file in old_files:
                        shutil.move(str(base_dir / old_file), str(archive_dir / old_file))
                    print(f"📁 Moved {len(old_files)} files to {archive_dir}")
        else:
            print("✅ No cleanup needed - migration complete!")
        return
    
    # Count files to migrate
    files_to_move = [(base_dir / old, base_dir / new) for old, new in file_moves.items() 
                     if (base_dir / old).exists()]
    
    if not files_to_move:
        print("⚠️  No files found to migrate!")
        print("   Either migration is complete or files are missing")
        return
    
    print(f"📋 Found {len(files_to_move)} files to migrate")
    
    if args.dry_run:
        print("\n🔍 Dry run - showing planned moves:")
        for old_path, new_path in files_to_move:
            print(f"   {old_path.name} → {new_path}")
        return
    
    # Create backup if requested
    if args.backup:
        for old_path, _ in files_to_move:
            backup_file = backup_dir / old_path.name
            shutil.copy2(str(old_path), str(backup_file))
        print(f"✅ Backed up {len(files_to_move)} files")
    
    # Perform migration
    moved_count = 0
    for old_path, new_path in files_to_move:
        try:
            # Ensure destination directory exists
            new_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Move the file
            shutil.move(str(old_path), str(new_path))
            print(f"✅ {old_path.name} → {new_path.parent.name}/")
            moved_count += 1
            
        except Exception as e:
            print(f"❌ Failed to move {old_path.name}: {e}")
    
    print(f"\n🎉 Migration complete! Moved {moved_count} files")
    print("\n📚 Next steps:")
    print("1. Test the new interface: python3 cd_manager.py --help")
    print("2. Try a command: python3 cd_manager.py report")
    print("3. Read the updated README.md for full documentation")
    
    if args.backup:
        print(f"4. Remove backup folder when satisfied: rm -rf {backup_dir}")

if __name__ == "__main__":
    main()
