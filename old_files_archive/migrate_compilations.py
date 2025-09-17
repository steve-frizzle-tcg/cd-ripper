#!/usr/bin/env python3
"""
Compilation Album Migration Utility
Identifies and migrates compilation albums to "Various Artists" folder structure.
"""

import json
import shutil
import re
from pathlib import Path
from mutagen.flac import FLAC

def identify_compilation_albums():
    """Identify albums that are likely compilations based on naming patterns"""
    output_dir = Path.home() / "cd_ripping" / "output"
    
    # Patterns that indicate compilation albums
    compilation_patterns = [
        r'.*classics.*',           # "Greatest Classics", "Rock Classics", etc.
        r'.*greatest.*hits.*',     # "Greatest Hits"
        r'.*best.*of.*',           # "Best of", "Very Best of"
        r'.*collection.*',         # "Collection", "Ultimate Collection"
        r'.*anthology.*',          # "Anthology"
        r'.*jock.*jams.*',         # "Jock Jams"
        r'.*wmmr.*',               # Radio station compilations
        r'.*espn.*',               # ESPN compilations
        r'.*woodstock.*',          # Festival compilations
        r'.*festival.*',           # Other festival compilations
        r'.*volume.*\d+.*',        # "Volume 1", "Vol. 2", etc.
        r'.*now.*that.*',          # "Now That's What I Call Music"
        r'.*various.*artists.*',   # Already marked as various artists
        r'.*no.*alternative.*',    # "No Alternative" compilation
        r'.*soundtrack.*',         # Soundtracks (though these go to Soundtracks folder)
        r'.*\d{3,4}.*',            # Radio station numbers like "933", "1065"
    ]
    
    potential_compilations = []
    
    # Skip these directories
    skip_dirs = {"Various Artists", "Soundtracks"}
    
    for item in output_dir.iterdir():
        if not item.is_dir() or item.name in skip_dirs:
            continue
            
        # Check if name matches compilation patterns
        is_compilation = False
        matched_pattern = None
        
        for pattern in compilation_patterns:
            if re.search(pattern, item.name, re.IGNORECASE):
                is_compilation = True
                matched_pattern = pattern
                # Exclude "311" as it's a band name, not a compilation
                if item.name == "311":
                    is_compilation = False
                break
        
        if is_compilation:
            # Check if this is an album directory (has FLAC files) or artist directory (has subdirs)
            flac_files = list(item.glob("*.flac"))
            subdirs = [x for x in item.iterdir() if x.is_dir()]
            
            if flac_files:
                # This is an album directory itself - treat as single album compilation
                potential_compilations.append({
                    'album_dir': item,
                    'album_name': item.name,
                    'pattern': matched_pattern,
                    'is_album_dir': True,
                    'track_count': len(flac_files),
                    'type': 'album'
                })
            elif subdirs:
                # This is an artist directory with album subdirectories
                album_names = [x.name for x in subdirs[:3]]  # First 3 albums
                potential_compilations.append({
                    'artist_dir': item,
                    'artist_name': item.name,
                    'pattern': matched_pattern,
                    'is_album_dir': False,
                    'album_count': len(subdirs),
                    'sample_albums': album_names,
                    'type': 'artist'
                })
    
    return potential_compilations

def check_if_has_multiple_artists(album_dir):
    """Check if an album has multiple artists in the tracks (indicates compilation)"""
    rip_info_path = album_dir / "rip_info.json"
    
    if not rip_info_path.exists():
        return False, []
    
    try:
        with open(rip_info_path, 'r', encoding='utf-8') as f:
            rip_info = json.load(f)
        
        tracks = rip_info.get('metadata', {}).get('tracks', [])
        if not tracks:
            return False, []
        
        # Get unique artists from tracks
        artists = set()
        for track in tracks:
            artist = track.get('artist', '').strip()
            if artist and artist != 'Unknown Artist':
                artists.add(artist)
        
        return len(artists) > 1, list(artists)
        
    except Exception as e:
        print(f"   ⚠️  Could not read metadata for {album_dir.name}: {e}")
        return False, []

def migrate_album_to_various_artists(album_dir):
    """Migrate a single album directory to Various Artists"""
    output_dir = Path.home() / "cd_ripping" / "output"
    various_artists_dir = output_dir / "Various Artists"
    
    # Create Various Artists directory
    various_artists_dir.mkdir(exist_ok=True)
    
    album_name = album_dir.name
    target_album_dir = various_artists_dir / album_name
    
    # Check if target already exists
    if target_album_dir.exists():
        print(f"   ⚠️  Skipping '{album_name}' - already exists in Various Artists")
        return False
    
    print(f"   🎵 Moving: {album_name}")
    
    try:
        # Move the album directory
        shutil.move(str(album_dir), str(target_album_dir))
        
        # Update metadata
        rip_info_path = target_album_dir / "rip_info.json"
        if rip_info_path.exists():
            with open(rip_info_path, 'r', encoding='utf-8') as f:
                rip_info = json.load(f)
            
            # Update album artist to Various Artists
            if 'metadata' in rip_info:
                rip_info['metadata']['album_artist'] = 'Various Artists'
                # Keep individual track artists as they are
            
            with open(rip_info_path, 'w', encoding='utf-8') as f:
                json.dump(rip_info, f, indent=2, ensure_ascii=False)
        
        # Update FLAC files
        flac_files = list(target_album_dir.glob("*.flac"))
        for flac_file in flac_files:
            try:
                audio = FLAC(flac_file)
                # Set album artist to Various Artists, keep track artists
                audio['ALBUMARTIST'] = ['Various Artists']
                audio.save()
            except Exception as e:
                print(f"      ❌ Failed to update {flac_file.name}: {e}")
        
        print(f"      ✅ Migrated successfully")
        return True
        
    except Exception as e:
        print(f"      ❌ Failed to migrate '{album_name}': {e}")
        return False

def migrate_to_various_artists(compilations_to_migrate):
    """Migrate selected compilations to Various Artists"""
    print(f"\n🚚 Starting migration to Various Artists...")
    
    total_albums_migrated = 0
    
    for comp_info in compilations_to_migrate:
        if comp_info['type'] == 'album':
            # Single album compilation
            album_dir = comp_info['album_dir']
            album_name = comp_info['album_name']
            
            print(f"\n📁 Migrating album: {album_name}")
            
            if migrate_album_to_various_artists(album_dir):
                total_albums_migrated += 1
                
        elif comp_info['type'] == 'artist':
            # Artist directory with multiple albums
            artist_dir = comp_info['artist_dir']
            artist_name = comp_info['artist_name']
            
            print(f"\n📁 Migrating artist: {artist_name}")
            
            # Get all albums
            albums = [x for x in artist_dir.iterdir() if x.is_dir()]
            
            for album_dir in albums:
                if migrate_album_to_various_artists(album_dir):
                    total_albums_migrated += 1
            
            # Clean up empty artist directory
            try:
                if artist_dir.exists() and not any(artist_dir.iterdir()):
                    artist_dir.rmdir()
                    print(f"   🧹 Removed empty directory: {artist_name}")
            except OSError as e:
                print(f"   ⚠️  Could not remove directory {artist_name}: {e}")
    
    print(f"\n✅ Migration complete! Moved {total_albums_migrated} albums to Various Artists")
    return total_albums_migrated

def main():
    """Main entry point"""
    print("=== Compilation Album Migration Utility ===")
    print("This tool identifies compilation albums and moves them to 'Various Artists' folder")
    
    # Find potential compilations
    print("\n🔍 Scanning for compilation albums...")
    potential_compilations = identify_compilation_albums()
    
    if not potential_compilations:
        print("✅ No compilation albums found!")
        return 0
    
    print(f"\n📋 Found {len(potential_compilations)} potential compilations:")
    
    # Analyze each potential compilation
    confirmed_compilations = []
    
    for i, comp in enumerate(potential_compilations, 1):
        if comp['type'] == 'album':
            print(f"\n{i}. {comp['album_name']} ({comp['track_count']} tracks)")
            print(f"   Pattern matched: {comp['pattern']}")
            
            # Check if album has multiple artists
            has_multiple, artists = check_if_has_multiple_artists(comp['album_dir'])
            if has_multiple:
                print(f"   🎵 Multiple artists: {', '.join(artists[:5])}{'...' if len(artists) > 5 else ''}")
                print(f"   ✅ Confirmed compilation (multiple artists detected)")
            else:
                print(f"   ❓ Possible compilation (based on name pattern only)")
            
            confirmed_compilations.append(comp)
            
        elif comp['type'] == 'artist':
            print(f"\n{i}. {comp['artist_name']} ({comp['album_count']} albums)")
            print(f"   Pattern matched: {comp['pattern']}")
            print(f"   Sample albums: {', '.join(comp['sample_albums'])}")
            
            # Check if albums have multiple artists
            multiple_artists_found = False
            for album_name in comp['sample_albums']:
                album_dir = comp['artist_dir'] / album_name
                if album_dir.exists():
                    has_multiple, artists = check_if_has_multiple_artists(album_dir)
                    if has_multiple:
                        print(f"   🎵 '{album_name}' has multiple artists: {', '.join(artists[:3])}{'...' if len(artists) > 3 else ''}")
                        multiple_artists_found = True
                        break
            
            if multiple_artists_found:
                print(f"   ✅ Confirmed compilation (multiple artists detected)")
            else:
                print(f"   ❓ Possible compilation (based on name pattern only)")
            
            confirmed_compilations.append(comp)
    
    if not confirmed_compilations:
        print("\n❌ No confirmed compilations found")
        return 0
    
    # Let user select which ones to migrate
    print(f"\n📋 Select compilations to migrate to 'Various Artists':")
    print("Enter numbers separated by spaces (e.g., '1 3 5'), 'all' for all, or 'none' to cancel")
    
    selection = input("Selection: ").strip().lower()
    
    if selection == 'none':
        print("❌ Migration cancelled")
        return 0
    
    selected_compilations = []
    
    if selection == 'all':
        selected_compilations = confirmed_compilations
    else:
        try:
            indices = [int(x.strip()) for x in selection.split()]
            for idx in indices:
                if 1 <= idx <= len(confirmed_compilations):
                    selected_compilations.append(confirmed_compilations[idx - 1])
                else:
                    print(f"⚠️  Invalid selection: {idx}")
        except ValueError:
            print("❌ Invalid input format")
            return 1
    
    if not selected_compilations:
        print("❌ No compilations selected")
        return 1
    
    # Show summary
    total_albums = 0
    print(f"\n📊 Will migrate {len(selected_compilations)} compilation(s):")
    for comp in selected_compilations:
        if comp['type'] == 'album':
            print(f"   - {comp['album_name']} (1 album)")
            total_albums += 1
        elif comp['type'] == 'artist':
            print(f"   - {comp['artist_name']} ({comp['album_count']} albums)")
            total_albums += comp['album_count']
    
    print(f"\nTotal albums to migrate: {total_albums}")
    
    # Final confirmation
    confirm = input(f"\nProceed with migration? (y/n): ").lower().strip()
    if confirm not in ['y', 'yes']:
        print("❌ Migration cancelled")
        return 0
    
    # Perform migration
    migrated_count = migrate_to_various_artists(selected_compilations)
    
    print(f"\n🎉 Successfully migrated {migrated_count} albums!")
    print("You can now find them under 'Various Artists' folder")
    
    return 0

if __name__ == "__main__":
    import sys
    sys.exit(main())
