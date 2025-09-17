#!/usr/bin/env python3
"""
Single Album Metadata Updater
Updates a specific album with proper track names and metadata from Discogs/MusicBrainz.
"""

import sys
import json
from pathlib import Path
from typing import Dict, List, Optional
from mutagen.flac import FLAC

def update_annie_lennox_walking_on_broken_glass():
    """Update the Annie Lennox Walking On Broken Glass single with proper metadata"""
    
    album_dir = Path("output/Annie Lenox/Walking On Broken Glass")
    
    if not album_dir.exists():
        print(f"❌ Album directory not found: {album_dir}")
        return False
    
    # Proper track information from Discogs US Maxi-Single (ID: 1512000)
    track_info = {
        1: {
            "title": "Walking On Broken Glass (Single Version)",
            "artist": "Annie Lennox",
            "duration": "3:59"
        },
        2: {
            "title": "It's Alright (Baby's Comin' Back)",
            "artist": "Annie Lennox", 
            "duration": "4:13"
        },
        3: {
            "title": "River Deep, Mountain High",
            "artist": "Annie Lennox",
            "duration": "3:30"
        },
        4: {
            "title": "Here Comes The Rain Again",
            "artist": "Annie Lennox",
            "duration": "4:39"
        },
        5: {
            "title": "Walking On Broken Glass",
            "artist": "Annie Lennox",
            "duration": "3:50"
        }
    }
    
    # Enhanced album metadata
    album_metadata = {
        "album": "Walking On Broken Glass",
        "albumartist": "Annie Lennox",
        "artist": "Annie Lennox",
        "date": "1992",
        "genre": "Pop Rock, Synth-pop",
        "style": "Pop Rock",
        "country": "US",
        "mediatype": "CD (Maxi-Single)",
        "label": "Arista",
        "discogs_release_id": "1512000",
        "musicbrainz_albumid": "e7fb0062-a5ed-4f97-9de4-ef3978dcf594",
        "totaltracks": "5",
        "totaldiscs": "1",
        "discnumber": "1"
    }
    
    print(f"🎵 Updating Annie Lennox - Walking On Broken Glass")
    print("=" * 60)
    
    # Process each track
    success_count = 0
    for track_num in range(1, 6):
        old_filename = f"Track_{track_num:02d}.flac"
        old_path = album_dir / old_filename
        
        if not old_path.exists():
            print(f"❌ Track {track_num} file not found: {old_filename}")
            continue
        
        track_data = track_info[track_num]
        
        # Create new filename with proper disc-track format
        new_filename = f"01-{track_num:02d}. {track_data['title']}.flac"
        # Clean filename for filesystem
        new_filename = clean_filename(new_filename)
        new_path = album_dir / new_filename
        
        print(f"\n📀 Track {track_num}: {track_data['title']}")
        
        try:
            # Load FLAC file
            audio = FLAC(old_path)
            
            # Update metadata
            for key, value in album_metadata.items():
                audio[key] = value
            
            # Track-specific metadata
            audio["title"] = track_data["title"]
            audio["artist"] = track_data["artist"]
            audio["tracknumber"] = f"01-{track_num:02d}"
            
            # Save metadata
            audio.save()
            
            # Rename file if needed
            if old_path != new_path:
                old_path.rename(new_path)
                print(f"  📝 Renamed: {old_filename} → {new_filename}")
            
            print(f"  ✅ Updated metadata: {track_data['title']}")
            success_count += 1
            
        except Exception as e:
            print(f"  ❌ Failed to update track {track_num}: {e}")
    
    # Update rip_info.json
    try:
        rip_info_path = album_dir / "rip_info.json"
        
        if rip_info_path.exists():
            with open(rip_info_path, 'r') as f:
                rip_info = json.load(f)
        else:
            rip_info = {}
        
        # Update rip_info with enhanced metadata
        rip_info["metadata"] = {
            "artist": "Annie Lennox",
            "album": "Walking On Broken Glass",
            "date": "1992",
            "mbid": "e7fb0062-a5ed-4f97-9de4-ef3978dcf594",
            "discogs_id": "1512000",
            "method": "discogs_enhanced",
            "album_type": "single",
            "genre": "Pop Rock, Synth-pop",
            "country": "US",
            "label": "Arista"
        }
        
        rip_info["tracks"] = []
        for track_num in range(1, 6):
            track_data = track_info[track_num]
            rip_info["tracks"].append({
                "track_number": track_num,
                "title": track_data["title"],
                "artist": track_data["artist"],
                "duration": track_data["duration"]
            })
        
        rip_info["total_tracks"] = 5
        rip_info["cover_art"] = None  # Will be updated when cover is added
        
        with open(rip_info_path, 'w') as f:
            json.dump(rip_info, f, indent=2)
        
        print(f"\n✅ Updated rip_info.json with enhanced metadata")
        
    except Exception as e:
        print(f"\n❌ Failed to update rip_info.json: {e}")
    
    print(f"\n📊 Results: {success_count}/5 tracks updated successfully")
    
    if success_count == 5:
        print("✅ Album metadata update complete!")
        print("🎨 You can now add cover art using:")
        print(f"   python3 discogs_cover_manager.py output")
        return True
    else:
        print("⚠️  Some tracks failed to update")
        return False

def clean_filename(filename: str) -> str:
    """Clean filename for filesystem compatibility"""
    # Replace problematic characters
    replacements = {
        '/': '-',
        '\\': '-',
        ':': ' -',
        '*': '',
        '?': '',
        '"': "'",
        '<': '(',
        '>': ')',
        '|': '-'
    }
    
    for old, new in replacements.items():
        filename = filename.replace(old, new)
    
    # Remove multiple spaces and clean up
    filename = ' '.join(filename.split())
    
    return filename

def main():
    """Main function"""
    print("🎵 Single Album Metadata Updater")
    print("=" * 50)
    
    if len(sys.argv) > 1 and sys.argv[1] == "--annie-lennox":
        success = update_annie_lennox_walking_on_broken_glass()
        if success:
            print("\n🎯 Next steps:")
            print("1. Add cover art: python3 discogs_cover_manager.py output")
            print("2. Verify updates: python3 cover_art_report.py output")
        sys.exit(0 if success else 1)
    else:
        print("Usage: python3 single_metadata_updater.py --annie-lennox")
        print("\nAvailable single updates:")
        print("  --annie-lennox    Update Annie Lennox - Walking On Broken Glass")
        sys.exit(1)

if __name__ == "__main__":
    main()
