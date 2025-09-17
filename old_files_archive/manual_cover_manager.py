#!/usr/bin/env python3
"""
Manual Cover Art Manager
Add cover art to albums by providing image files manually.
"""

import os
import sys
import json
from pathlib import Path
from mutagen.flac import FLAC, Picture
import mimetypes
import shutil
from PIL import Image
import argparse

class ManualCoverManager:
    def __init__(self, output_dir: str):
        self.output_dir = Path(output_dir)
    
    def find_album(self, artist: str, album: str) -> Path:
        """Find album directory"""
        artist_dir = self.output_dir / artist
        if not artist_dir.exists():
            # Try case-insensitive search
            for d in self.output_dir.iterdir():
                if d.is_dir() and d.name.lower() == artist.lower():
                    artist_dir = d
                    break
            else:
                raise FileNotFoundError(f"Artist directory not found: {artist}")
        
        album_dir = artist_dir / album
        if not album_dir.exists():
            # Try case-insensitive search
            for d in artist_dir.iterdir():
                if d.is_dir() and d.name.lower() == album.lower():
                    album_dir = d
                    break
            else:
                raise FileNotFoundError(f"Album directory not found: {album}")
        
        return album_dir
    
    def validate_image(self, image_path: str) -> bool:
        """Validate image file"""
        try:
            with Image.open(image_path) as img:
                print(f"   📐 Image size: {img.size[0]}x{img.size[1]}")
                print(f"   🎨 Format: {img.format}")
                
                # Check if it's a reasonable album cover size
                width, height = img.size
                if width < 200 or height < 200:
                    print(f"   ⚠️  Image might be too small for album cover")
                    return input("   Continue anyway? (y/n): ").lower().startswith('y')
                
                if width > 2000 or height > 2000:
                    print(f"   ℹ️  Large image - will be used as-is")
                
                return True
        except Exception as e:
            print(f"   ❌ Invalid image file: {e}")
            return False
    
    def resize_image_if_needed(self, image_path: str, max_size: int = 1000) -> str:
        """Resize image if it's too large"""
        try:
            with Image.open(image_path) as img:
                if max(img.size) > max_size:
                    # Calculate new size maintaining aspect ratio
                    ratio = max_size / max(img.size)
                    new_size = tuple(int(dim * ratio) for dim in img.size)
                    
                    # Resize image
                    resized_img = img.resize(new_size, Image.Resampling.LANCZOS)
                    
                    # Save resized image
                    resized_path = str(Path(image_path).with_suffix('.resized' + Path(image_path).suffix))
                    resized_img.save(resized_path, quality=95)
                    
                    print(f"   📏 Resized image to {new_size[0]}x{new_size[1]}: {resized_path}")
                    return resized_path
                else:
                    return image_path
        except Exception as e:
            print(f"   ⚠️  Error resizing image: {e}")
            return image_path
    
    def add_cover_to_album(self, artist: str, album: str, image_path: str, resize: bool = True) -> bool:
        """Add cover art to album"""
        try:
            # Find album directory
            album_dir = self.find_album(artist, album)
            print(f"📁 Found album: {album_dir}")
            
            # Validate image
            if not self.validate_image(image_path):
                return False
            
            # Resize if needed
            if resize:
                image_path = self.resize_image_if_needed(image_path)
            
            # Copy image to album directory
            image_file = Path(image_path)
            cover_filename = f"cover{image_file.suffix}"
            cover_path = album_dir / cover_filename
            
            shutil.copy2(image_path, cover_path)
            print(f"✅ Copied cover image: {cover_path}")
            
            # Add to FLAC files
            if self.add_cover_to_flac_files(str(album_dir), str(cover_path)):
                # Update rip_info.json
                self.update_rip_info_cover(str(album_dir), cover_filename)
                print(f"🎵 Cover art added successfully!")
                return True
            else:
                print(f"❌ Failed to add cover to FLAC files")
                return False
                
        except Exception as e:
            print(f"❌ Error adding cover: {e}")
            return False
    
    def add_cover_to_flac_files(self, album_path: str, cover_image_path: str) -> bool:
        """Add cover art to all FLAC files in album"""
        try:
            album_dir = Path(album_path)
            cover_path = Path(cover_image_path)
            
            if not cover_path.exists():
                print(f"⚠️  Cover image not found: {cover_path}")
                return False
            
            # Read cover image
            with open(cover_path, 'rb') as f:
                cover_data = f.read()
            
            # Determine MIME type
            mime_type = mimetypes.guess_type(str(cover_path))[0]
            if not mime_type:
                mime_type = 'image/jpeg'  # Default
            
            # Create picture object
            picture = Picture()
            picture.data = cover_data
            picture.type = 3  # Cover (front)
            picture.desc = 'Cover'
            picture.mime = mime_type
            
            # Add to all FLAC files
            flac_files = list(album_dir.glob("*.flac"))
            updated_count = 0
            
            for flac_file in flac_files:
                try:
                    audio = FLAC(flac_file)
                    # Clear existing pictures
                    audio.clear_pictures()
                    # Add new picture
                    audio.add_picture(picture)
                    audio.save()
                    updated_count += 1
                except Exception as e:
                    print(f"⚠️  Error updating {flac_file.name}: {e}")
            
            print(f"✅ Added cover art to {updated_count}/{len(flac_files)} FLAC files")
            return updated_count > 0
            
        except Exception as e:
            print(f"❌ Error adding cover to FLAC files: {e}")
            return False
    
    def update_rip_info_cover(self, album_path: str, cover_filename: str) -> bool:
        """Update rip_info.json with cover art information"""
        try:
            rip_info_path = Path(album_path) / "rip_info.json"
            
            if rip_info_path.exists():
                with open(rip_info_path, 'r', encoding='utf-8') as f:
                    rip_info = json.load(f)
                
                rip_info['cover_art'] = cover_filename
                
                with open(rip_info_path, 'w', encoding='utf-8') as f:
                    json.dump(rip_info, f, indent=2, ensure_ascii=False)
                
                print(f"✅ Updated rip_info.json with cover_art: {cover_filename}")
                return True
            else:
                print(f"⚠️  No rip_info.json found in {album_path}")
                return False
                
        except Exception as e:
            print(f"❌ Error updating rip_info.json: {e}")
            return False
    
    def list_missing_covers(self) -> None:
        """List albums missing covers"""
        print("🔍 Scanning for albums missing cover art...")
        missing_count = 0
        
        for artist_dir in self.output_dir.iterdir():
            if not artist_dir.is_dir():
                continue
                
            for album_dir in artist_dir.iterdir():
                if not album_dir.is_dir():
                    continue
                
                # Check for existing cover files
                cover_files = list(album_dir.glob("cover.*")) + list(album_dir.glob("folder.*"))
                has_cover_file = len(cover_files) > 0
                
                # Check for embedded cover art in FLAC files
                flac_files = list(album_dir.glob("*.flac"))
                has_embedded_cover = False
                
                if flac_files:
                    try:
                        audio = FLAC(flac_files[0])
                        has_embedded_cover = len(audio.pictures) > 0
                    except:
                        pass
                
                if not (has_cover_file or has_embedded_cover):
                    missing_count += 1
                    print(f"❌ {artist_dir.name} / {album_dir.name}")
        
        print(f"\n📊 Found {missing_count} albums missing cover art")

def main():
    parser = argparse.ArgumentParser(description='Manual Cover Art Manager')
    parser.add_argument('--output-dir', default='output', help='Output directory')
    parser.add_argument('--list', action='store_true', help='List albums missing covers')
    parser.add_argument('--artist', help='Artist name')
    parser.add_argument('--album', help='Album name')
    parser.add_argument('--image', help='Path to cover image file')
    parser.add_argument('--no-resize', action='store_true', help='Skip image resizing')
    
    args = parser.parse_args()
    
    if not os.path.exists(args.output_dir):
        print(f"❌ Output directory not found: {args.output_dir}")
        return 1
    
    manager = ManualCoverManager(args.output_dir)
    
    if args.list:
        manager.list_missing_covers()
        return 0
    
    if args.artist and args.album and args.image:
        if not os.path.exists(args.image):
            print(f"❌ Image file not found: {args.image}")
            return 1
        
        print(f"=== Manual Cover Art Manager ===")
        print(f"Adding cover to: {args.artist} / {args.album}")
        print(f"Image file: {args.image}")
        print()
        
        success = manager.add_cover_to_album(
            args.artist, 
            args.album, 
            args.image, 
            resize=not args.no_resize
        )
        
        if success:
            print(f"🎉 Cover art added successfully!")
            return 0
        else:
            print(f"❌ Failed to add cover art")
            return 1
    
    # Interactive mode
    print(f"=== Manual Cover Art Manager ===")
    print(f"Add cover art to albums manually")
    print()
    
    manager.list_missing_covers()
    print()
    
    print(f"To add cover art:")
    print(f"python3 {sys.argv[0]} --artist \"Artist Name\" --album \"Album Name\" --image \"/path/to/cover.jpg\"")
    print()
    print(f"Example:")
    print(f"python3 {sys.argv[0]} --artist \"Annie Lenox\" --album \"Walking On Broken Glass\" --image \"~/Downloads/cover.jpg\"")
    print()
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
