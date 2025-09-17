#!/usr/bin/env python3
"""
Find Missing Album Covers Tool
Identifies albums without cover art and provides options to find/add covers.
"""

import os
import sys
import json
from pathlib import Path
from mutagen.flac import FLAC
from typing import List, Dict, Tuple
import requests
import time
from urllib.parse import quote

class MissingCoversFinder:
    def __init__(self, output_dir: str):
        self.output_dir = Path(output_dir)
        self.missing_covers = []
        
    def scan_for_missing_covers(self) -> List[Dict]:
        """Scan all albums for missing cover art"""
        print("🔍 Scanning for albums missing cover art...")
        missing_covers = []
        
        for artist_dir in self.output_dir.iterdir():
            if not artist_dir.is_dir():
                continue
                
            for album_dir in artist_dir.iterdir():
                if not album_dir.is_dir():
                    continue
                    
                album_path = album_dir
                artist_name = artist_dir.name
                album_name = album_dir.name
                
                # Check for existing cover files
                cover_files = list(album_path.glob("cover.*")) + list(album_path.glob("folder.*"))
                has_cover_file = len(cover_files) > 0
                
                # Check for embedded cover art in FLAC files
                flac_files = list(album_path.glob("*.flac"))
                has_embedded_cover = False
                
                if flac_files:
                    try:
                        audio = FLAC(flac_files[0])
                        has_embedded_cover = len(audio.pictures) > 0
                    except Exception as e:
                        print(f"⚠️  Error reading {flac_files[0]}: {e}")
                
                # Check rip_info.json for cover_art field
                rip_info_path = album_path / "rip_info.json"
                has_rip_info_cover = False
                rip_info_data = None
                
                if rip_info_path.exists():
                    try:
                        with open(rip_info_path, 'r', encoding='utf-8') as f:
                            rip_info_data = json.load(f)
                            cover_art_path = rip_info_data.get('cover_art')
                            if cover_art_path and Path(album_path / cover_art_path).exists():
                                has_rip_info_cover = True
                    except Exception as e:
                        print(f"⚠️  Error reading rip_info.json for {artist_name}/{album_name}: {e}")
                
                # Determine if album is missing covers
                if not (has_cover_file or has_embedded_cover or has_rip_info_cover):
                    missing_info = {
                        'artist': artist_name,
                        'album': album_name,
                        'path': str(album_path),
                        'flac_count': len(flac_files),
                        'rip_info': rip_info_data
                    }
                    missing_covers.append(missing_info)
                    print(f"❌ {artist_name} / {album_name}")
                else:
                    # Optionally show albums with covers for verification
                    cover_status = []
                    if has_cover_file:
                        cover_status.append("file")
                    if has_embedded_cover:
                        cover_status.append("embedded")
                    if has_rip_info_cover:
                        cover_status.append("rip_info")
                    # print(f"✅ {artist_name} / {album_name} ({', '.join(cover_status)})")
        
        self.missing_covers = missing_covers
        return missing_covers
    
    def search_discogs_cover(self, artist: str, album: str) -> List[Dict]:
        """Search Discogs for album cover"""
        try:
            # Simple search using Discogs API
            search_url = "https://api.discogs.com/database/search"
            params = {
                'q': f'"{artist}" "{album}"',
                'type': 'release',
                'format': 'CD'
            }
            
            headers = {
                'User-Agent': 'CDRipper/1.0 +https://github.com/steve-frizzle-tcg/cd-ripper'
            }
            
            response = requests.get(search_url, params=params, headers=headers)
            if response.status_code == 200:
                data = response.json()
                results = []
                
                for result in data.get('results', [])[:5]:  # Top 5 results
                    results.append({
                        'title': result.get('title', ''),
                        'year': result.get('year', ''),
                        'thumb': result.get('thumb', ''),
                        'resource_url': result.get('resource_url', ''),
                        'id': result.get('id', '')
                    })
                
                return results
            else:
                print(f"⚠️  Discogs API error: {response.status_code}")
                return []
                
        except Exception as e:
            print(f"⚠️  Error searching Discogs: {e}")
            return []
    
    def download_cover_image(self, image_url: str, save_path: str) -> bool:
        """Download cover image from URL"""
        try:
            headers = {
                'User-Agent': 'CDRipper/1.0 +https://github.com/steve-frizzle-tcg/cd-ripper'
            }
            
            response = requests.get(image_url, headers=headers)
            if response.status_code == 200:
                with open(save_path, 'wb') as f:
                    f.write(response.content)
                return True
            else:
                print(f"⚠️  Failed to download image: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"⚠️  Error downloading image: {e}")
            return False
    
    def add_cover_to_flac_files(self, album_path: str, cover_image_path: str) -> bool:
        """Add cover art to all FLAC files in album"""
        try:
            from mutagen.flac import FLAC, Picture
            import mimetypes
            
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
            print(f"⚠️  Error adding cover to FLAC files: {e}")
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
            print(f"⚠️  Error updating rip_info.json: {e}")
            return False

def main():
    if len(sys.argv) > 1:
        output_dir = sys.argv[1]
    else:
        output_dir = "output"
    
    if not os.path.exists(output_dir):
        print(f"❌ Output directory not found: {output_dir}")
        return 1
    
    finder = MissingCoversFinder(output_dir)
    
    print("=== Missing Album Covers Finder ===")
    print("Identifies albums without cover art")
    print()
    
    # Scan for missing covers
    missing_covers = finder.scan_for_missing_covers()
    
    print(f"\n📊 Scan Results:")
    print(f"   ❌ Albums without covers: {len(missing_covers)}")
    
    if not missing_covers:
        print("🎉 All albums have cover art!")
        return 0
    
    print(f"\n📋 Albums Missing Cover Art:")
    for i, album in enumerate(missing_covers, 1):
        print(f"   {i:3d}. {album['artist']} / {album['album']} ({album['flac_count']} tracks)")
    
    print(f"\nChoose operation:")
    print(f"1. Show detailed missing covers list")
    print(f"2. Interactive cover finder (search and download)")
    print(f"3. Batch search for covers (show Discogs results)")
    print(f"4. Export missing covers list to JSON")
    
    try:
        choice = input("Enter choice (1-4): ").strip()
        
        if choice == "1":
            # Detailed list
            for album in missing_covers:
                print(f"\n📁 {album['artist']} / {album['album']}")
                print(f"   Path: {album['path']}")
                print(f"   FLAC files: {album['flac_count']}")
                if album['rip_info']:
                    print(f"   Has rip_info.json: Yes")
                    if 'catalog_number' in album['rip_info']:
                        print(f"   Catalog: {album['rip_info']['catalog_number']}")
                else:
                    print(f"   Has rip_info.json: No")
        
        elif choice == "2":
            # Interactive cover finder
            print(f"\n🔍 Interactive Cover Finder")
            for i, album in enumerate(missing_covers):
                print(f"\n📁 [{i+1}/{len(missing_covers)}] {album['artist']} / {album['album']}")
                
                # Search Discogs
                print("   Searching Discogs...")
                results = finder.search_discogs_cover(album['artist'], album['album'])
                
                if results:
                    print(f"   Found {len(results)} results:")
                    for j, result in enumerate(results, 1):
                        print(f"   {j}. {result['title']} ({result['year']})")
                        if result['thumb']:
                            print(f"      Image: {result['thumb']}")
                    
                    # User choice
                    try:
                        choice = input(f"   Download cover? (1-{len(results)}, s=skip, q=quit): ").strip().lower()
                        
                        if choice == 'q':
                            break
                        elif choice == 's':
                            continue
                        elif choice.isdigit() and 1 <= int(choice) <= len(results):
                            selected = results[int(choice) - 1]
                            
                            if selected['thumb']:
                                # Download cover
                                cover_filename = "cover.jpg"
                                cover_path = Path(album['path']) / cover_filename
                                
                                print(f"   Downloading: {selected['thumb']}")
                                if finder.download_cover_image(selected['thumb'], str(cover_path)):
                                    print(f"   ✅ Downloaded: {cover_path}")
                                    
                                    # Add to FLAC files
                                    if finder.add_cover_to_flac_files(album['path'], str(cover_path)):
                                        # Update rip_info.json
                                        finder.update_rip_info_cover(album['path'], cover_filename)
                                        print(f"   ✅ Cover art added successfully!")
                                    else:
                                        print(f"   ⚠️  Failed to add cover to FLAC files")
                                else:
                                    print(f"   ❌ Failed to download cover")
                            else:
                                print(f"   ⚠️  No image URL available")
                        else:
                            print(f"   ⚠️  Invalid choice")
                            
                    except KeyboardInterrupt:
                        print(f"\n\n⏹️  Interrupted by user")
                        break
                    except Exception as e:
                        print(f"   ⚠️  Error: {e}")
                else:
                    print(f"   ❌ No results found")
                
                # Rate limiting
                time.sleep(1)
        
        elif choice == "3":
            # Batch search
            print(f"\n🔍 Batch Search Results:")
            for album in missing_covers:
                print(f"\n📁 {album['artist']} / {album['album']}")
                results = finder.search_discogs_cover(album['artist'], album['album'])
                
                if results:
                    print(f"   Found {len(results)} results:")
                    for result in results[:3]:  # Top 3
                        print(f"   • {result['title']} ({result['year']})")
                        if result['thumb']:
                            print(f"     {result['thumb']}")
                else:
                    print(f"   ❌ No results found")
                
                time.sleep(1)  # Rate limiting
        
        elif choice == "4":
            # Export to JSON
            export_path = "missing_covers.json"
            with open(export_path, 'w', encoding='utf-8') as f:
                json.dump(missing_covers, f, indent=2, ensure_ascii=False)
            print(f"✅ Exported missing covers list to: {export_path}")
        
        else:
            print(f"❌ Invalid choice")
            return 1
            
    except KeyboardInterrupt:
        print(f"\n\n⏹️  Interrupted by user")
        return 0
    except Exception as e:
        print(f"❌ Error: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
