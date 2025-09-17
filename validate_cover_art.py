#!/usr/bin/env python3
"""
Cover Art Field Validator and Fixer
Validates and fixes the cover_art field in rip_info.json files to match actual cover art files.
"""

import json
import os
from pathlib import Path
from typing import Dict, List, Optional, Tuple

class CoverArtValidator:
    def __init__(self, output_dir: str = None):
        self.output_dir = Path(output_dir) if output_dir else Path.home() / "cd_ripping" / "output"
        
        # Common cover art filenames to look for
        self.cover_patterns = [
            "cover.jpg", "cover.jpeg", "cover.png", "cover.gif", "cover.bmp",
            "folder.jpg", "folder.jpeg", "folder.png", "folder.gif", "folder.bmp",
            "front.jpg", "front.jpeg", "front.png", "front.gif", "front.bmp",
            "albumart.jpg", "albumart.jpeg", "albumart.png", "albumart.gif", "albumart.bmp",
            "album.jpg", "album.jpeg", "album.png", "album.gif", "album.bmp"
        ]

    def find_cover_art_files(self, album_dir: Path) -> List[Path]:
        """Find all potential cover art files in an album directory"""
        cover_files = []
        
        for pattern in self.cover_patterns:
            matches = list(album_dir.glob(pattern))
            cover_files.extend(matches)
        
        # Also check for any image files that might be cover art
        for ext in ['*.jpg', '*.jpeg', '*.png', '*.gif', '*.bmp']:
            image_files = list(album_dir.glob(ext))
            for img in image_files:
                # Add any image files not already found
                if img not in cover_files and img.name.lower() not in [f.name.lower() for f in cover_files]:
                    cover_files.append(img)
        
        return sorted(cover_files, key=lambda x: self.get_cover_priority(x.name))

    def get_cover_priority(self, filename: str) -> int:
        """Get priority score for cover art files (lower = higher priority)"""
        filename_lower = filename.lower()
        
        if filename_lower.startswith('cover.'):
            return 1
        elif filename_lower.startswith('folder.'):
            return 2
        elif filename_lower.startswith('front.'):
            return 3
        elif filename_lower.startswith('albumart.'):
            return 4
        elif filename_lower.startswith('album.'):
            return 5
        else:
            return 10  # Other image files get lowest priority

    def get_best_cover_art(self, album_dir: Path) -> Optional[str]:
        """Get the best cover art file for an album directory"""
        cover_files = self.find_cover_art_files(album_dir)
        
        if not cover_files:
            return None
        
        # Return the highest priority cover file
        return str(cover_files[0])

    def validate_cover_art_field(self, rip_info_path: Path) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Validate the cover_art field in a rip_info.json file
        Returns: (needs_update, current_value, correct_value)
        """
        try:
            with open(rip_info_path, 'r', encoding='utf-8') as f:
                rip_info = json.load(f)
            
            album_dir = rip_info_path.parent
            current_cover_art = rip_info.get('cover_art')
            
            # Find the actual best cover art file
            correct_cover_art = self.get_best_cover_art(album_dir)
            
            # Check if update is needed
            needs_update = False
            
            if current_cover_art is None and correct_cover_art is not None:
                # Cover art exists but field is None/missing
                needs_update = True
            elif current_cover_art is not None and correct_cover_art is None:
                # Field points to cover art but no file exists
                needs_update = True
            elif current_cover_art is not None and correct_cover_art is not None:
                # Both exist, check if they match
                current_path = Path(current_cover_art)
                correct_path = Path(correct_cover_art)
                
                # Handle both absolute and relative paths
                if current_path.is_absolute():
                    needs_update = current_path != correct_path
                else:
                    # Current is relative, compare to correct relative path
                    correct_relative = correct_path.relative_to(album_dir.parent.parent) if len(correct_path.parts) > 2 else correct_path.name
                    needs_update = str(current_path) != str(correct_relative)
            
            return needs_update, current_cover_art, correct_cover_art
            
        except Exception as e:
            print(f"   ❌ Error reading {rip_info_path}: {e}")
            return False, None, None

    def update_cover_art_field(self, rip_info_path: Path, new_cover_art: Optional[str]) -> bool:
        """Update the cover_art field in a rip_info.json file"""
        try:
            with open(rip_info_path, 'r', encoding='utf-8') as f:
                rip_info = json.load(f)
            
            # Update the cover_art field
            rip_info['cover_art'] = new_cover_art
            
            # Add update timestamp
            rip_info['cover_art_updated'] = __import__('time').strftime("%Y-%m-%d %H:%M:%S")
            
            # Write back to file
            with open(rip_info_path, 'w', encoding='utf-8') as f:
                json.dump(rip_info, f, indent=2, ensure_ascii=False)
            
            return True
            
        except Exception as e:
            print(f"   ❌ Error updating {rip_info_path}: {e}")
            return False

    def find_all_rip_info_files(self) -> List[Path]:
        """Find all rip_info.json files in the output directory"""
        rip_info_files = []
        
        print("🔍 Scanning for rip_info.json files...")
        
        # Skip the top-level directories we know aren't artists
        skip_dirs = {'.git', '__pycache__', 'logs', 'temp'}
        
        # Scan all directories in output
        for item in self.output_dir.iterdir():
            if not item.is_dir() or item.name in skip_dirs:
                continue
            
            # Check if this directory has a rip_info.json (Various Artists albums)
            rip_info_file = item / "rip_info.json"
            if rip_info_file.exists():
                rip_info_files.append(rip_info_file)
            
            # Check subdirectories for artist/album structure
            for subdir in item.iterdir():
                if subdir.is_dir():
                    sub_rip_info = subdir / "rip_info.json"
                    if sub_rip_info.exists():
                        rip_info_files.append(sub_rip_info)
        
        return sorted(rip_info_files)

    def validate_all_cover_art_fields(self, fix_issues: bool = False) -> Dict[str, int]:
        """Validate cover_art fields in all rip_info.json files"""
        rip_info_files = self.find_all_rip_info_files()
        
        stats = {
            'total_files': len(rip_info_files),
            'correct': 0,
            'missing_cover_field': 0,
            'missing_cover_file': 0,
            'incorrect_path': 0,
            'fixed': 0,
            'errors': 0
        }
        
        print(f"📋 Found {len(rip_info_files)} rip_info.json files to validate")
        
        for rip_info_path in rip_info_files:
            album_path = rip_info_path.parent
            relative_path = album_path.relative_to(self.output_dir)
            
            try:
                needs_update, current_value, correct_value = self.validate_cover_art_field(rip_info_path)
                
                if not needs_update:
                    stats['correct'] += 1
                    continue
                
                # Determine the type of issue
                issue_type = ""
                if current_value is None and correct_value is not None:
                    issue_type = "missing_cover_field"
                    stats['missing_cover_field'] += 1
                elif current_value is not None and correct_value is None:
                    issue_type = "missing_cover_file"
                    stats['missing_cover_file'] += 1
                elif current_value != correct_value:
                    issue_type = "incorrect_path"
                    stats['incorrect_path'] += 1
                
                print(f"\n📁 {relative_path}")
                print(f"   ❌ Issue: {issue_type}")
                print(f"   📄 Current: {current_value}")
                print(f"   ✅ Should be: {correct_value}")
                
                # Show available cover files
                cover_files = self.find_cover_art_files(album_path)
                if cover_files:
                    print(f"   🖼️  Available covers: {[f.name for f in cover_files]}")
                
                if fix_issues:
                    if self.update_cover_art_field(rip_info_path, correct_value):
                        stats['fixed'] += 1
                        print(f"   ✅ Fixed cover_art field")
                    else:
                        stats['errors'] += 1
                        print(f"   ❌ Failed to fix cover_art field")
                
            except Exception as e:
                stats['errors'] += 1
                print(f"\n📁 {relative_path}")
                print(f"   ❌ Error processing: {e}")
        
        return stats

def main():
    """Main entry point"""
    print("=== Cover Art Field Validator ===")
    print("This tool validates and optionally fixes cover_art fields in rip_info.json files")
    
    validator = CoverArtValidator()
    
    print("\nChoose an action:")
    print("1. Validate only (show issues without fixing)")
    print("2. Validate and fix issues")
    
    while True:
        choice = input("Enter choice (1-2): ").strip()
        if choice in ['1', '2']:
            break
        print("Please enter 1 or 2")
    
    fix_issues = (choice == '2')
    
    if fix_issues:
        print("\n⚠️  This will modify rip_info.json files")
        confirm = input("Continue? (y/n): ").lower().strip()
        if confirm not in ['y', 'yes']:
            print("❌ Operation cancelled")
            return 0
    
    print(f"\n🚀 {'Validating and fixing' if fix_issues else 'Validating'} cover_art fields...")
    
    stats = validator.validate_all_cover_art_fields(fix_issues=fix_issues)
    
    print(f"\n📊 Validation Results:")
    print(f"   📋 Total files processed: {stats['total_files']}")
    print(f"   ✅ Correct: {stats['correct']}")
    print(f"   ❌ Issues found:")
    print(f"      - Missing cover_art field: {stats['missing_cover_field']}")
    print(f"      - Cover file missing: {stats['missing_cover_file']}")  
    print(f"      - Incorrect path: {stats['incorrect_path']}")
    
    if fix_issues:
        print(f"   🔧 Fixed: {stats['fixed']}")
        print(f"   ❌ Errors: {stats['errors']}")
        
        if stats['fixed'] > 0:
            print(f"\n🎉 Successfully fixed {stats['fixed']} cover_art fields!")
    else:
        total_issues = stats['missing_cover_field'] + stats['missing_cover_file'] + stats['incorrect_path']
        if total_issues > 0:
            print(f"\n💡 Run with option 2 to fix {total_issues} issues")
        else:
            print(f"\n🎉 All cover_art fields are correct!")
    
    return 0

if __name__ == "__main__":
    import sys
    sys.exit(main())
