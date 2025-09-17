#!/usr/bin/env python3
"""
Manual Cover Art Manager
Simple tool for adding cover art files to albums that are missing them.
"""

import os
import sys
import json
from pathlib import Path
from typing import Optional, List
from PIL import Image
from mutagen.flac import FLAC, Picture

class ManualCoverManager:
    """Simple manual cover art management"""
    
    def __init__(self):
        pass
    
    def find_missing_covers(self, output_dir: Path) -> List[Path]:
        """Find albums missing cover art files"""
        missing_covers = []
        
        for artist_dir in output_dir.iterdir():
            if not artist_dir.is_dir():
                continue
                
            for album_dir in artist_dir.iterdir():
                if not album_dir.is_dir():
                    continue
                
                # Check for cover files
                cover_files = list(album_dir.glob('cover.*')) + list(album_dir.glob('folder.*'))
                
                if not cover_files:
                    missing_covers.append(album_dir)
        
        return missing_covers
    
    def add_cover_to_album(self, album_dir: Path, cover_file: Path) -> bool:
        """Add a cover file to an album directory and FLAC files"""
        try:
            # Validate image file
            try:
                with Image.open(cover_file) as img:
                    width, height = img.size
                    print(f"📸 Image dimensions: {width}x{height}")
                    
                    # Resize if too large
                    if width > 1000 or height > 1000:
                        print("🔄 Resizing image...")
                        img.thumbnail((1000, 1000), Image.Resampling.LANCZOS)
                        
                        # Save resized version
                        resized_path = album_dir / f"cover{cover_file.suffix}"
                        img.save(resized_path, optimize=True, quality=95)
                        final_cover_path = resized_path
                    else:
                        # Copy original
                        final_cover_path = album_dir / f"cover{cover_file.suffix}"
                        if cover_file != final_cover_path:
                            import shutil
                            shutil.copy2(cover_file, final_cover_path)
                        
            except Exception as e:
                print(f"❌ Invalid image file: {e}")
                return False
            
            print(f"✅ Cover saved: {final_cover_path}")
            
            # Add to FLAC files
            self.add_cover_to_flac_files(album_dir, final_cover_path)
            
            # Update rip_info.json if it exists
            rip_info_path = album_dir / 'rip_info.json'
            if rip_info_path.exists():
                try:
                    with open(rip_info_path, 'r') as f:
                        rip_info = json.load(f)
                    
                    rip_info['cover_art'] = final_cover_path.name
                    
                    with open(rip_info_path, 'w') as f:
                        json.dump(rip_info, f, indent=2)
                        
                    print("✅ Updated rip_info.json")
                except Exception as e:
                    print(f"⚠️  Could not update rip_info.json: {e}")
            
            return True
            
        except Exception as e:
            print(f"❌ Failed to add cover: {e}")
            return False
    
    def add_cover_to_flac_files(self, album_dir: Path, cover_path: Path):
        """Add cover art to all FLAC files in the album directory"""
        try:
            print("🎵 Adding cover art to FLAC files...")
            
            # Read cover image
            with open(cover_path, 'rb') as f:
                cover_data = f.read()
            
            # Determine MIME type
            if cover_path.suffix.lower() == '.png':
                mime_type = 'image/png'
            else:
                mime_type = 'image/jpeg'
            
            # Find all FLAC files
            flac_files = list(album_dir.glob('*.flac'))
            
            if not flac_files:
                print("❌ No FLAC files found in album directory")
                return
            
            updated_count = 0
            for flac_path in flac_files:
                try:
                    audio = FLAC(flac_path)
                    
                    # Clear existing pictures
                    audio.clear_pictures()
                    
                    # Create new picture
                    picture = Picture()
                    picture.type = 3  # Cover (front)
                    picture.mime = mime_type
                    picture.desc = 'Cover'
                    picture.data = cover_data
                    
                    # Add picture to FLAC
                    audio.add_picture(picture)
                    audio.save()
                    
                    updated_count += 1
                    
                except Exception as e:
                    print(f"❌ Failed to update {flac_path.name}: {e}")
            
            print(f"✅ Updated {updated_count}/{len(flac_files)} FLAC files with cover art")
            
        except Exception as e:
            print(f"❌ Failed to add cover art to FLAC files: {e}")
    
    def interactive_add_covers(self, missing_albums: List[Path]):
        """Interactive session to add covers to albums"""
        print(f"\n🎵 Interactive Cover Addition")
        print("=" * 50)
        
        for i, album_dir in enumerate(missing_albums):
            artist = album_dir.parent.name
            album = album_dir.name
            
            print(f"\n📁 [{i+1}/{len(missing_albums)}] {artist} / {album}")
            print(f"   Location: {album_dir}")
            
            while True:
                print("\nOptions:")
                print("1. Add cover file from path")
                print("2. Skip this album")
                print("3. Exit")
                
                choice = input("Choose option (1-3): ").strip()
                
                if choice == '1':
                    cover_path = input("Enter path to cover image file: ").strip()
                    cover_file = Path(cover_path)
                    
                    if not cover_file.exists():
                        print("❌ File does not exist")
                        continue
                    
                    if not cover_file.suffix.lower() in ['.jpg', '.jpeg', '.png']:
                        print("❌ File must be JPG or PNG")
                        continue
                    
                    if self.add_cover_to_album(album_dir, cover_file):
                        print("✅ Cover added successfully!")
                        break
                    else:
                        print("❌ Failed to add cover")
                        
                elif choice == '2':
                    print("⏭️  Skipping album")
                    break
                elif choice == '3':
                    print("👋 Exiting")
                    return
                else:
                    print("Invalid choice. Please enter 1, 2, or 3.")


def main():
    """Main function"""
    if len(sys.argv) != 2:
        print("Usage: python3 manual_cover_manager.py <output_directory>")
        print("Example: python3 manual_cover_manager.py output")
        sys.exit(1)
    
    output_dir = Path(sys.argv[1])
    if not output_dir.exists():
        print(f"❌ Output directory does not exist: {output_dir}")
        sys.exit(1)
    
    manager = ManualCoverManager()
    
    # Find missing covers
    print("🔍 Scanning for albums missing cover art...")
    missing_covers = manager.find_missing_covers(output_dir)
    
    if not missing_covers:
        print("✅ All albums have cover art!")
        return
    
    print(f"\n📋 Found {len(missing_covers)} albums missing cover art:")
    for album_dir in missing_covers:
        artist = album_dir.parent.name
        album = album_dir.name
        print(f"   • {artist} / {album}")
    
    # Interactive session
    manager.interactive_add_covers(missing_covers)


if __name__ == "__main__":
    main()
