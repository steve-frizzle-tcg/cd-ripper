#!/usr/bin/env python3
"""
Manual Cover Art Updater
Updates cover art for a specific album with a provided image file.
"""

import sys
import json
from pathlib import Path
from typing import Optional
from PIL import Image
from mutagen.flac import FLAC, Picture

def update_cover_art(album_dir: Path, new_cover_path: Path) -> bool:
    """Update cover art for an album with a new image file"""
    
    if not album_dir.exists():
        print(f"❌ Album directory not found: {album_dir}")
        return False
    
    if not new_cover_path.exists():
        print(f"❌ Cover image not found: {new_cover_path}")
        return False
    
    print(f"🎨 Updating cover art for: {album_dir.parent.name} / {album_dir.name}")
    print("=" * 80)
    
    try:
        # Validate and process the image
        with Image.open(new_cover_path) as img:
            width, height = img.size
            format_name = img.format
            file_size = new_cover_path.stat().st_size
            
            print(f"📸 New image: {width}x{height} {format_name} ({file_size/1024:.1f} KB)")
            
            # Resize if too large
            if width > 1000 or height > 1000:
                print("🔄 Resizing image...")
                img = img.convert('RGB') if img.mode != 'RGB' else img
                img.thumbnail((1000, 1000), Image.Resampling.LANCZOS)
                
                # Save resized version
                temp_path = album_dir / "cover_resized.jpg"
                img.save(temp_path, 'JPEG', optimize=True, quality=95)
                final_cover_path = temp_path
            else:
                # Use original or convert to RGB if needed
                if img.mode != 'RGB':
                    img = img.convert('RGB')
                    temp_path = album_dir / "cover_converted.jpg"
                    img.save(temp_path, 'JPEG', optimize=True, quality=95)
                    final_cover_path = temp_path
                else:
                    final_cover_path = new_cover_path
        
        # Copy to album directory as cover.jpg
        target_path = album_dir / "cover.jpg"
        
        if final_cover_path != target_path:
            if final_cover_path.name.startswith("cover_"):
                # It's our temp file, just rename it
                final_cover_path.rename(target_path)
            else:
                # Copy the original file
                import shutil
                shutil.copy2(final_cover_path, target_path)
        
        print(f"✅ Cover saved: {target_path}")
        
        # Update FLAC files
        success_count = update_flac_cover_art(album_dir, target_path)
        
        # Update rip_info.json
        update_rip_info_cover(album_dir, "cover.jpg")
        
        print(f"\n📊 Results: Updated {success_count} FLAC files with new cover art")
        return success_count > 0
        
    except Exception as e:
        print(f"❌ Failed to process image: {e}")
        return False

def update_flac_cover_art(album_dir: Path, cover_path: Path) -> int:
    """Update cover art in all FLAC files"""
    try:
        print("🎵 Updating FLAC files...")
        
        # Read cover image
        with open(cover_path, 'rb') as f:
            cover_data = f.read()
        
        # Find all FLAC files
        flac_files = list(album_dir.glob('*.flac'))
        
        if not flac_files:
            print("❌ No FLAC files found")
            return 0
        
        updated_count = 0
        for flac_path in flac_files:
            try:
                audio = FLAC(flac_path)
                
                # Clear existing pictures
                audio.clear_pictures()
                
                # Create new picture
                picture = Picture()
                picture.type = 3  # Cover (front)
                picture.mime = 'image/jpeg'
                picture.desc = 'Cover'
                picture.data = cover_data
                
                # Add picture to FLAC
                audio.add_picture(picture)
                audio.save()
                
                updated_count += 1
                print(f"  ✅ {flac_path.name}")
                
            except Exception as e:
                print(f"  ❌ Failed to update {flac_path.name}: {e}")
        
        return updated_count
        
    except Exception as e:
        print(f"❌ Failed to update FLAC files: {e}")
        return 0

def update_rip_info_cover(album_dir: Path, cover_filename: str):
    """Update rip_info.json with cover art information"""
    rip_info_path = album_dir / 'rip_info.json'
    
    if rip_info_path.exists():
        try:
            with open(rip_info_path, 'r') as f:
                rip_info = json.load(f)
            
            rip_info['cover_art'] = cover_filename
            
            with open(rip_info_path, 'w') as f:
                json.dump(rip_info, f, indent=2)
                
            print(f"📝 Updated rip_info.json")
            
        except Exception as e:
            print(f"⚠️  Could not update rip_info.json: {e}")

def main():
    """Main function"""
    if len(sys.argv) != 3:
        print("Usage: python3 manual_cover_updater.py <album_directory> <cover_image_file>")
        print("Example: python3 manual_cover_updater.py \"output/Annie Lenox/Walking On Broken Glass\" ~/Downloads/correct_cover.jpg")
        sys.exit(1)
    
    album_dir = Path(sys.argv[1])
    cover_file = Path(sys.argv[2])
    
    print("🎨 Manual Cover Art Updater")
    print("=" * 50)
    
    success = update_cover_art(album_dir, cover_file)
    
    if success:
        print("\n✅ Cover art update complete!")
        print("🔍 Verify with: python3 cover_art_report.py output")
    else:
        print("\n❌ Cover art update failed")
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
