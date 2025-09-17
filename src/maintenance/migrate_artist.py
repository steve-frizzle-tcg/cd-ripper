#!/usr/bin/env python3
"""
General artist name migration utility.
Helps migrate albums from one artist name to another, updating all metadata.
"""

import json
import shutil
import sys
from pathlib import Path
from mutagen.flac import FLAC

def list_available_artists():
    """List all artists in the output directory"""
    output_dir = Path.home() / "cd_ripping" / "output"
    if not output_dir.exists():
        print("❌ Output directory not found")
        return []
    
    artists = []
    for item in output_dir.iterdir():
        if item.is_dir() and item.name != "Soundtracks":
            album_count = len([x for x in item.iterdir() if x.is_dir()])
            artists.append((item.name, album_count))
    
    return sorted(artists)

def migrate_artist(old_name: str, new_name: str):
    """Migrate all albums from old artist name to new artist name"""
    output_dir = Path.home() / "cd_ripping" / "output"
    old_artist_dir = output_dir / old_name
    new_artist_dir = output_dir / new_name
    
    print(f"=== Artist Migration: '{old_name}' → '{new_name}' ===")
    
    # Check if source exists
    if not old_artist_dir.exists():
        print(f"❌ Artist '{old_name}' not found")
        return False
    
    # Get albums to migrate
    albums = [item for item in old_artist_dir.iterdir() if item.is_dir()]
    if not albums:
        print(f"❌ No albums found for '{old_name}'")
        return False
    
    print(f"📁 Found {len(albums)} albums to migrate:")
    for album in albums:
        print(f"   - {album.name}")
    
    # Check if destination already has albums
    if new_artist_dir.exists():
        existing_albums = [item.name for item in new_artist_dir.iterdir() if item.is_dir()]
        if existing_albums:
            print(f"⚠️  '{new_name}' already has albums: {existing_albums}")
            print("   Albums will be merged into existing directory")
    
    # Confirm migration
    confirm = input(f"\nMigrate {len(albums)} albums to '{new_name}'? (y/n): ").lower().strip()
    if confirm not in ['y', 'yes']:
        print("❌ Migration cancelled")
        return False
    
    try:
        # Create new artist directory
        new_artist_dir.mkdir(exist_ok=True)
        
        # Migrate each album
        migrated_albums = 0
        for album_dir in albums:
            album_name = album_dir.name
            new_album_dir = new_artist_dir / album_name
            
            if new_album_dir.exists():
                print(f"⚠️  Skipping '{album_name}' - already exists in destination")
                continue
            
            print(f"\n🚚 Migrating: {album_name}")
            
            # Move album directory
            shutil.move(str(album_dir), str(new_album_dir))
            
            # Update rip_info.json
            rip_info_path = new_album_dir / "rip_info.json"
            if rip_info_path.exists():
                with open(rip_info_path, 'r', encoding='utf-8') as f:
                    rip_info = json.load(f)
                
                if 'metadata' in rip_info:
                    rip_info['metadata']['artist'] = new_name
                    rip_info['metadata']['album_artist'] = new_name
                    
                    # Update track artists
                    for track in rip_info['metadata'].get('tracks', []):
                        if track.get('artist') == old_name:
                            track['artist'] = new_name
                
                with open(rip_info_path, 'w', encoding='utf-8') as f:
                    json.dump(rip_info, f, indent=2, ensure_ascii=False)
                
                print(f"   ✅ Updated rip_info.json")
            
            # Update FLAC files
            flac_files = list(new_album_dir.glob("*.flac"))
            if flac_files:
                print(f"   🎵 Updating {len(flac_files)} FLAC files...")
                for flac_file in flac_files:
                    try:
                        audio = FLAC(flac_file)
                        
                        if 'ARTIST' in audio and audio['ARTIST'][0] == old_name:
                            audio['ARTIST'] = [new_name]
                        
                        if 'ALBUMARTIST' in audio:
                            audio['ALBUMARTIST'] = [new_name]
                        
                        audio.save()
                    except Exception as e:
                        print(f"   ❌ Failed to update {flac_file.name}: {e}")
                
                print(f"   ✅ Updated FLAC metadata")
            
            migrated_albums += 1
        
        # Clean up old directory
        if old_artist_dir.exists():
            try:
                if not any(old_artist_dir.iterdir()):
                    old_artist_dir.rmdir()
                    print(f"\n🧹 Removed empty directory: '{old_name}'")
                else:
                    remaining = [item.name for item in old_artist_dir.iterdir()]
                    print(f"\n⚠️  '{old_name}' directory not empty: {remaining}")
            except OSError as e:
                print(f"⚠️  Could not remove old directory: {e}")
        
        print(f"\n✅ Migration complete!")
        print(f"📁 Migrated {migrated_albums} albums to '{new_name}'")
        return True
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        return False

def main():
    """Main entry point"""
    print("=== Artist Name Migration Utility ===")
    
    # List available artists
    artists = list_available_artists()
    if not artists:
        print("❌ No artists found")
        return 1
    
    print(f"\n📁 Available artists ({len(artists)} total):")
    for name, album_count in artists:
        print(f"   - {name} ({album_count} albums)")
    
    print(f"\nEnter artist names to migrate:")
    old_name = input("From (current artist name): ").strip()
    new_name = input("To (new artist name): ").strip()
    
    if not old_name or not new_name:
        print("❌ Both names are required")
        return 1
    
    if old_name == new_name:
        print("❌ Names cannot be the same")
        return 1
    
    success = migrate_artist(old_name, new_name)
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())
