#!/usr/bin/env python3
"""
Retroactive rip_info.json Generator
Creates rip_info.json files for existing albums by extracting metadata from FLAC files.
"""

import json
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from mutagen.flac import FLAC

class RipInfoGenerator:
    def __init__(self, output_dir: str = None):
        self.output_dir = Path(output_dir) if output_dir else Path.home() / "cd_ripping" / "output"
        
    def extract_flac_metadata(self, flac_path: Path) -> Dict:
        """Extract metadata from a FLAC file"""
        try:
            audio = FLAC(str(flac_path))
            
            # Helper function to get first value from potentially multi-value fields
            def get_first(field_list):
                if isinstance(field_list, list) and field_list:
                    return field_list[0]
                elif isinstance(field_list, str):
                    return field_list
                return ""
            
            metadata = {
                'title': get_first(audio.get('TITLE', [''])),
                'artist': get_first(audio.get('ARTIST', [''])),
                'album': get_first(audio.get('ALBUM', [''])),
                'album_artist': get_first(audio.get('ALBUMARTIST', [''])),
                'date': get_first(audio.get('DATE', [''])),
                'track_number': get_first(audio.get('TRACKNUMBER', [''])),
                'disc_number': get_first(audio.get('DISCNUMBER', ['1'])),
                'total_tracks': get_first(audio.get('TOTALTRACKS', [''])),
                'total_discs': get_first(audio.get('TOTALDISCS', ['1'])),
                'mbid': get_first(audio.get('MUSICBRAINZ_ALBUMID', ['']))
            }
            
            # Get file duration if available
            if hasattr(audio, 'info') and hasattr(audio.info, 'length'):
                metadata['length'] = int(audio.info.length * 1000)  # Convert to milliseconds
            
            return metadata
            
        except Exception as e:
            print(f"   ❌ Error reading {flac_path.name}: {e}")
            return {}

    def analyze_album_directory(self, album_dir: Path) -> Optional[Dict]:
        """Analyze an album directory and extract comprehensive metadata"""
        # Check if rip_info.json already exists
        if (album_dir / "rip_info.json").exists():
            return None  # Skip albums that already have rip_info.json
        
        # Find FLAC files
        flac_files = sorted(album_dir.glob("*.flac"))
        if not flac_files:
            return None  # No FLAC files found
        
        print(f"   📀 Analyzing: {album_dir.name} ({len(flac_files)} tracks)")
        
        # Extract metadata from all FLAC files
        tracks_metadata = []
        album_metadata = {}
        artists_set = set()
        
        for flac_file in flac_files:
            track_meta = self.extract_flac_metadata(flac_file)
            if track_meta:
                tracks_metadata.append({
                    'filename': flac_file.name,
                    'metadata': track_meta
                })
                
                # Collect album-level metadata from first track
                if not album_metadata:
                    album_metadata = {
                        'album': track_meta.get('album', album_dir.name),
                        'album_artist': track_meta.get('album_artist', ''),
                        'date': track_meta.get('date', ''),
                        'mbid': track_meta.get('mbid', ''),
                        'total_discs': track_meta.get('total_discs', '1')
                    }
                
                # Collect unique artists
                artist = track_meta.get('artist', '').strip()
                if artist:
                    artists_set.add(artist)
        
        if not tracks_metadata:
            return None
        
        # Determine album type and artist information
        unique_artists = list(artists_set)
        is_various_artists = len(unique_artists) > 1 or album_metadata.get('album_artist', '').lower() == 'various artists'
        
        # Determine album type based on directory structure and metadata
        album_type = 'regular'
        parent_dir_name = album_dir.parent.name
        
        if parent_dir_name == 'Soundtracks':
            album_type = 'soundtrack'
        elif parent_dir_name == 'Various Artists' or is_various_artists:
            album_type = 'compilation'
        
        # Set final artist and album_artist
        if is_various_artists:
            final_artist = 'Various Artists'
            final_album_artist = 'Various Artists'
        else:
            final_artist = album_metadata.get('album_artist') or unique_artists[0] if unique_artists else parent_dir_name
            final_album_artist = final_artist
        
        # Build track list
        tracks = []
        for i, track_data in enumerate(tracks_metadata, 1):
            track_meta = track_data['metadata']
            
            # Parse track number (handle disc-track format like "01-05")
            track_num_str = track_meta.get('track_number', str(i))
            disc_num = 1
            track_num = i
            
            if '-' in track_num_str:
                parts = track_num_str.split('-')
                if len(parts) == 2:
                    try:
                        disc_num = int(parts[0])
                        track_num = int(parts[1])
                    except ValueError:
                        pass
            else:
                try:
                    track_num = int(track_num_str)
                except ValueError:
                    pass
            
            track_info = {
                'title': track_meta.get('title', f'Track {track_num:02d}'),
                'length': track_meta.get('length'),
                'disc_number': disc_num,
                'track_number': track_num,
                'filename': track_data['filename']
            }
            
            # Add individual artist for Various Artists releases
            if is_various_artists:
                track_info['artist'] = track_meta.get('artist', 'Unknown Artist')
            
            tracks.append(track_info)
        
        # Check for cover art
        cover_files = list(album_dir.glob("cover.*")) + list(album_dir.glob("folder.*"))
        cover_path = str(cover_files[0]) if cover_files else None
        
        # Build the rip_info structure
        rip_info = {
            'metadata': {
                'artist': final_artist,
                'album': album_metadata['album'],
                'album_artist': final_album_artist,
                'date': album_metadata['date'],
                'album_type': album_type,
                'disc_count': int(album_metadata.get('total_discs', 1)),
                'mbid': album_metadata['mbid'] if album_metadata['mbid'] else 'retroactive-scan',
                'method': 'retroactive-scan',
                'tracks': tracks
            },
            'rip_date': 'retroactive-scan',
            'tracks_ripped': len(tracks_metadata),
            'total_tracks': len(tracks_metadata),
            'cover_art': cover_path,
            'device': 'unknown',
            'generated_by': 'retroactive_rip_info_generator',
            'generated_date': time.strftime("%Y-%m-%d %H:%M:%S")
        }
        
        return rip_info

    def find_albums_without_rip_info(self) -> List[Path]:
        """Find all album directories that don't have rip_info.json"""
        albums_without_rip_info = []
        
        print("🔍 Scanning for albums without rip_info.json...")
        
        # Skip the top-level directories we know aren't artists
        skip_dirs = {'.git', '__pycache__', 'logs', 'temp'}
        
        # Scan all directories in output
        for item in self.output_dir.iterdir():
            if not item.is_dir() or item.name in skip_dirs:
                continue
            
            # Check if this is an artist directory or direct album directory
            subdirs = [x for x in item.iterdir() if x.is_dir()]
            flac_files = list(item.glob("*.flac"))
            
            if flac_files and not (item / "rip_info.json").exists():
                # This is a direct album directory (like Various Artists albums)
                albums_without_rip_info.append(item)
            elif subdirs:
                # This is an artist directory, check each album subdirectory
                for album_dir in subdirs:
                    album_flac_files = list(album_dir.glob("*.flac"))
                    if album_flac_files and not (album_dir / "rip_info.json").exists():
                        albums_without_rip_info.append(album_dir)
        
        return albums_without_rip_info

    def generate_rip_info_files(self, albums: List[Path], confirm_each: bool = False) -> int:
        """Generate rip_info.json files for the specified albums"""
        generated_count = 0
        
        for album_dir in albums:
            try:
                print(f"\n📁 Processing: {album_dir.parent.name}/{album_dir.name}")
                
                rip_info = self.analyze_album_directory(album_dir)
                if not rip_info:
                    print(f"   ⏭️  Skipped (no FLAC files or already has rip_info.json)")
                    continue
                
                # Show summary
                metadata = rip_info['metadata']
                print(f"   🎵 Album: {metadata['album']}")
                print(f"   🎤 Artist: {metadata['artist']}")
                print(f"   📅 Date: {metadata['date']}")
                print(f"   🏷️  Type: {metadata['album_type']}")
                print(f"   💿 Tracks: {len(metadata['tracks'])}")
                
                if metadata['album_type'] in ['soundtrack', 'compilation']:
                    unique_artists = set(track.get('artist', '') for track in metadata['tracks'] if track.get('artist'))
                    print(f"   🎭 Artists: {len(unique_artists)} unique artists")
                
                if confirm_each:
                    response = input("   Generate rip_info.json? (y/n/all): ").lower().strip()
                    if response == 'n':
                        continue
                    elif response == 'all':
                        confirm_each = False
                
                # Write the rip_info.json file
                rip_info_path = album_dir / "rip_info.json"
                with open(rip_info_path, 'w', encoding='utf-8') as f:
                    json.dump(rip_info, f, indent=2, ensure_ascii=False)
                
                print(f"   ✅ Generated rip_info.json")
                generated_count += 1
                
            except Exception as e:
                print(f"   ❌ Error processing {album_dir}: {e}")
                continue
        
        return generated_count

def main():
    """Main entry point"""
    print("=== Retroactive rip_info.json Generator ===")
    print("This tool creates rip_info.json files for existing albums by reading FLAC metadata")
    
    generator = RipInfoGenerator()
    
    # Find albums without rip_info.json
    albums = generator.find_albums_without_rip_info()
    
    if not albums:
        print("\n✅ All albums already have rip_info.json files!")
        return 0
    
    print(f"\n📋 Found {len(albums)} albums without rip_info.json:")
    
    # Show sample of albums found
    for i, album_dir in enumerate(albums[:10], 1):
        flac_count = len(list(album_dir.glob("*.flac")))
        print(f"   {i:2d}. {album_dir.parent.name}/{album_dir.name} ({flac_count} tracks)")
    
    if len(albums) > 10:
        print(f"   ... and {len(albums) - 10} more albums")
    
    print(f"\nThis will generate rip_info.json files containing:")
    print(f"   - Album metadata extracted from FLAC files")
    print(f"   - Track listings with titles and artist information")
    print(f"   - Album type detection (regular/soundtrack/compilation)")
    print(f"   - Cover art references (if present)")
    
    # Get user confirmation
    response = input(f"\nProceed with generating {len(albums)} rip_info.json files? (y/n/confirm-each): ").lower().strip()
    
    if response == 'n':
        print("❌ Operation cancelled")
        return 0
    
    confirm_each = response == 'confirm-each'
    
    # Generate the files
    print(f"\n🚀 Generating rip_info.json files...")
    generated_count = generator.generate_rip_info_files(albums, confirm_each=confirm_each)
    
    print(f"\n🎉 Generated {generated_count} rip_info.json files!")
    print(f"You can now:")
    print(f"   - Use consistent metadata across all albums")
    print(f"   - Run bulk metadata enrichment scripts")
    print(f"   - Perform album-wide operations more easily")
    
    return 0

if __name__ == "__main__":
    import sys
    sys.exit(main())
