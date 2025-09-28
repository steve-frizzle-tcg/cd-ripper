#!/usr/bin/env python3
"""
Metadata Correction Tool
Fixes albums that received incorrect MusicBrainz metadata during ripping.

This tool helps correct cases where:
1. The wrong album was matched from MusicBrainz
2. Multiple albums have similar names 
3. The automatic matching picked the wrong release

Usage:
    python3 metadata_corrector.py "/path/to/album"
    python3 metadata_corrector.py "/path/to/album" --search "Artist - Album Title"
    python3 metadata_corrector.py "/path/to/album" --mbid "musicbrainz-id" --apply
"""

import argparse
import json
import sys
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from mutagen.flac import FLAC
import musicbrainzngs
import requests

# Configure MusicBrainz
musicbrainzngs.set_useragent(
    "CD-Ripper-MetadataCorrector", 
    "1.0", 
    "https://github.com/steve-frizzle-tcg/cd-ripper"
)

class MetadataCorrector:
    def __init__(self, album_path: str):
        self.album_path = Path(album_path)
        self.rip_info_path = self.album_path / "rip_info.json"
        
        if not self.album_path.exists() or not self.album_path.is_dir():
            raise ValueError(f"Album directory not found: {album_path}")
        
        if not self.rip_info_path.exists():
            raise ValueError(f"No rip_info.json found in {album_path}")
    
    def load_current_metadata(self) -> Dict:
        """Load current metadata from rip_info.json"""
        with open(self.rip_info_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def get_flac_files(self) -> List[Path]:
        """Get all FLAC files in the album directory"""
        return sorted(self.album_path.glob("*.flac"))
    
    def search_musicbrainz_releases(self, query: str, limit: int = 20) -> List[Dict]:
        """Search MusicBrainz for alternative releases"""
        try:
            print(f"🔍 Searching MusicBrainz: {query}")
            
            releases = musicbrainzngs.search_releases(query=query, limit=limit)
            
            if not releases.get('release-list'):
                return []
            
            # Enrich results with track count and detailed info
            enriched_releases = []
            
            for release in releases['release-list']:
                try:
                    # Get detailed release info
                    detailed = musicbrainzngs.get_release_by_id(
                        release['id'], 
                        includes=['recordings', 'media', 'artist-credits', 'labels']
                    )
                    
                    release_info = detailed['release']
                    
                    # Calculate track count
                    track_count = 0
                    if 'medium-list' in release_info:
                        for medium in release_info['medium-list']:
                            track_count += len(medium.get('track-list', []))
                    
                    # Get artist info
                    artist = "Unknown Artist"
                    if 'artist-credit' in release_info:
                        if len(release_info['artist-credit']) == 1:
                            artist = release_info['artist-credit'][0]['artist']['name']
                        else:
                            artist = "Various Artists"
                    
                    # Get label info
                    label = "Unknown Label"
                    if 'label-info-list' in release_info and release_info['label-info-list']:
                        label_info = release_info['label-info-list'][0]
                        if 'label' in label_info and label_info['label']:
                            label = label_info['label']['name']
                    
                    enriched_releases.append({
                        'mbid': release_info['id'],
                        'title': release_info['title'],
                        'artist': artist,
                        'date': release_info.get('date', 'Unknown'),
                        'country': release_info.get('country', 'Unknown'),
                        'label': label,
                        'track_count': track_count,
                        'barcode': release_info.get('barcode', ''),
                        'status': release_info.get('status', 'Unknown'),
                        'detailed_info': release_info
                    })
                    
                except Exception as e:
                    print(f"   ⚠️  Could not get details for release {release['id']}: {e}")
                    continue
            
            return enriched_releases
            
        except Exception as e:
            print(f"❌ MusicBrainz search failed: {e}")
            return []
    
    def display_release_options(self, releases: List[Dict], current_track_count: int) -> None:
        """Display release options for user selection"""
        print(f"\n📀 Found {len(releases)} possible matches:")
        print(f"   (Your CD has {current_track_count} tracks)\n")
        
        for i, release in enumerate(releases, 1):
            track_match = "✅" if release['track_count'] == current_track_count else "❌"
            
            print(f"{i:2d}. {release['title']}")
            print(f"    Artist: {release['artist']}")
            print(f"    Date: {release['date']}")
            print(f"    Country: {release['country']}")
            print(f"    Label: {release['label']}")
            print(f"    Tracks: {release['track_count']} {track_match}")
            print(f"    MBID: {release['mbid']}")
            
            if release['barcode']:
                print(f"    Barcode: {release['barcode']}")
            
            print()
    
    def select_release(self, releases: List[Dict]) -> Optional[Dict]:
        """Allow user to select the correct release"""
        while True:
            try:
                choice = input("Select the correct release (number), or 'q' to quit: ").strip().lower()
                
                if choice == 'q':
                    return None
                
                choice_num = int(choice)
                if 1 <= choice_num <= len(releases):
                    selected = releases[choice_num - 1]
                    
                    # Confirm selection
                    print(f"\n✅ Selected: {selected['title']} by {selected['artist']} ({selected['date']})")
                    confirm = input("Confirm this selection? (y/n): ").strip().lower()
                    
                    if confirm in ['y', 'yes']:
                        return selected
                    else:
                        continue
                else:
                    print(f"Please enter a number between 1 and {len(releases)}")
                    
            except ValueError:
                print("Please enter a valid number or 'q' to quit")
    
    def extract_detailed_metadata(self, release_info: Dict) -> Dict:
        """Extract comprehensive metadata from MusicBrainz release"""
        metadata = {
            'mbid': release_info['id'],
            'album': release_info['title'],
            'date': release_info.get('date', ''),
            'country': release_info.get('country', ''),
            'tracks': [],
            'disc_count': len(release_info.get('medium-list', [])),
            'method': 'metadata-corrector'
        }
        
        # Get artist information
        if 'artist-credit' in release_info:
            artist_credits = release_info['artist-credit']
            if len(artist_credits) == 1 and isinstance(artist_credits[0], dict):
                metadata['artist'] = artist_credits[0]['artist']['name']
                metadata['album_artist'] = artist_credits[0]['artist']['name']
            else:
                metadata['artist'] = 'Various Artists'
                metadata['album_artist'] = 'Various Artists'
        
        # Extract track information
        track_number = 1
        for disc_num, medium in enumerate(release_info.get('medium-list', []), 1):
            for track in medium.get('track-list', []):
                # Get track artist
                track_artist = metadata['artist']  # Default to album artist
                if 'artist-credit' in track:
                    track_credits = track['artist-credit']
                    if len(track_credits) == 1 and isinstance(track_credits[0], dict):
                        track_artist = track_credits[0]['artist']['name']
                    elif len(track_credits) > 1:
                        # Multiple artists, join them
                        artists = []
                        for credit in track_credits:
                            if isinstance(credit, dict) and 'artist' in credit:
                                artists.append(credit['artist']['name'])
                            elif isinstance(credit, str):
                                artists.append(credit)
                        track_artist = ' & '.join(artists) if artists else 'Various Artists'
                
                track_info = {
                    'number': track_number,
                    'disc': disc_num,
                    'title': track['recording']['title'],
                    'length': track['recording'].get('length'),
                    'mbid': track['recording']['id'],
                    'artist': track_artist,
                    'track_number': track_number,
                    'disc_number': disc_num
                }
                
                metadata['tracks'].append(track_info)
                track_number += 1
        
        return metadata
    
    def update_rip_info(self, new_metadata: Dict) -> None:
        """Update rip_info.json with corrected metadata"""
        current_data = self.load_current_metadata()
        
        # Update metadata section while preserving other fields
        current_data['metadata'].update({
            'album': new_metadata['album'],
            'artist': new_metadata['artist'],
            'album_artist': new_metadata['album_artist'],
            'date': new_metadata['date'],
            'mbid': new_metadata['mbid'],
            'tracks': new_metadata['tracks'],
            'disc_count': new_metadata['disc_count'],
            'method': new_metadata['method']
        })
        
        # Add correction timestamp
        current_data['correction_date'] = time.strftime("%Y-%m-%d %H:%M:%S")
        current_data['correction_tool'] = 'metadata_corrector'
        
        # Backup original file
        backup_path = self.rip_info_path.with_suffix('.json.backup')
        with open(backup_path, 'w', encoding='utf-8') as f:
            json.dump(self.load_current_metadata(), f, indent=2, ensure_ascii=False)
        
        print(f"📋 Backup created: {backup_path}")
        
        # Write updated metadata
        with open(self.rip_info_path, 'w', encoding='utf-8') as f:
            json.dump(current_data, f, indent=2, ensure_ascii=False)
        
        print(f"📝 Updated: {self.rip_info_path}")
    
    def apply_metadata_to_flacs(self, metadata: Dict) -> Tuple[int, List[str]]:
        """Apply corrected metadata to FLAC files"""
        flac_files = self.get_flac_files()
        tracks = metadata.get('tracks', [])
        
        updated_count = 0
        errors = []
        
        print(f"🎵 Applying metadata to {len(flac_files)} FLAC files...")
        
        for i, flac_file in enumerate(flac_files):
            try:
                audio = FLAC(str(flac_file))
                
                # Get track info (if available)
                track_info = tracks[i] if i < len(tracks) else {}
                
                # Apply album-level metadata
                audio['ALBUM'] = [metadata['album']]
                audio['ALBUMARTIST'] = [metadata['album_artist']]
                audio['DATE'] = [metadata['date']]
                audio['MUSICBRAINZ_ALBUMID'] = [metadata['mbid']]
                
                # Apply track-level metadata if available
                if track_info:
                    audio['TITLE'] = [track_info['title']]
                    audio['ARTIST'] = [track_info['artist']]
                    audio['TRACKNUMBER'] = [f"{track_info['disc']:02d}-{track_info['number']:02d}"]
                    audio['DISCNUMBER'] = [str(track_info['disc'])]
                    audio['MUSICBRAINZ_TRACKID'] = [track_info['mbid']]
                
                # Additional metadata
                audio['TOTALDISCS'] = [str(metadata['disc_count'])]
                audio['TOTALTRACKS'] = [str(len(tracks))]
                
                # Save changes
                audio.save()
                updated_count += 1
                
                print(f"   ✅ Updated: {flac_file.name}")
                
            except Exception as e:
                error_msg = f"Failed to update {flac_file.name}: {e}"
                errors.append(error_msg)
                print(f"   ❌ {error_msg}")
        
        return updated_count, errors
    
    def rename_files(self, metadata: Dict) -> Tuple[int, List[str]]:
        """Rename FLAC files to match corrected metadata"""
        flac_files = self.get_flac_files()
        tracks = metadata.get('tracks', [])
        
        renamed_count = 0
        errors = []
        
        print(f"📝 Renaming {len(flac_files)} FLAC files...")
        
        for i, flac_file in enumerate(flac_files):
            try:
                # Read current metadata from file
                audio = FLAC(str(flac_file))
                
                track_num = audio.get('TRACKNUMBER', [f'{i+1:02d}'])[0]
                title = audio.get('TITLE', ['Unknown Track'])[0]
                artist = audio.get('ARTIST', ['Unknown Artist'])[0]
                
                # Clean up filename components
                clean_title = title.replace('/', '_').replace('\\', '_').replace(':', '_')
                clean_artist = artist.replace('/', '_').replace('\\', '_').replace(':', '_')
                
                new_filename = f"{track_num}. {clean_artist} - {clean_title}.flac"
                new_path = flac_file.parent / new_filename
                
                # Only rename if name would change
                if flac_file.name != new_filename:
                    print(f"   📝 {flac_file.name}")
                    print(f"      → {new_filename}")
                    flac_file.rename(new_path)
                    renamed_count += 1
                else:
                    print(f"   ✓ {flac_file.name} (no change needed)")
                
            except Exception as e:
                error_msg = f"Failed to rename {flac_file.name}: {e}"
                errors.append(error_msg)
                print(f"   ❌ {error_msg}")
        
        return renamed_count, errors

def main():
    parser = argparse.ArgumentParser(
        description="Metadata Correction Tool - Fix incorrect MusicBrainz matches",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__.split('Usage:')[1].split('"""')[0] if 'Usage:' in __doc__ else ""
    )
    
    parser.add_argument('album_path', help='Path to album directory')
    parser.add_argument('--search', help='Custom search query (e.g., "Artist - Album Title")')
    parser.add_argument('--mbid', help='Specific MusicBrainz ID to apply')
    parser.add_argument('--apply', action='store_true', help='Apply changes (default is preview only)')
    parser.add_argument('--rename', action='store_true', help='Also rename files to match metadata')
    
    args = parser.parse_args()
    
    try:
        corrector = MetadataCorrector(args.album_path)
        
        print("🎵 Metadata Correction Tool")
        print("=" * 50)
        
        # Load current metadata
        current_data = corrector.load_current_metadata()
        current_metadata = current_data.get('metadata', {})
        
        print(f"📁 Album: {corrector.album_path}")
        print(f"🎼 Current: {current_metadata.get('artist', 'Unknown')} - {current_metadata.get('album', 'Unknown')}")
        print(f"📅 Date: {current_metadata.get('date', 'Unknown')}")
        print(f"🆔 MBID: {current_metadata.get('mbid', 'None')}")
        
        flac_count = len(corrector.get_flac_files())
        print(f"🎵 FLAC files: {flac_count}")
        
        if args.mbid:
            # Direct MBID application
            print(f"\n🎯 Applying specific MusicBrainz ID: {args.mbid}")
            
            try:
                release = musicbrainzngs.get_release_by_id(
                    args.mbid, 
                    includes=['recordings', 'media', 'artist-credits', 'labels']
                )
                
                new_metadata = corrector.extract_detailed_metadata(release['release'])
                
                print(f"✅ Found: {new_metadata['artist']} - {new_metadata['album']} ({new_metadata['date']})")
                print(f"📊 Tracks: {len(new_metadata['tracks'])}")
                
                if not args.apply:
                    print("\n📋 Preview mode - use --apply to make changes")
                    return 0
                
                # Apply changes
                corrector.update_rip_info(new_metadata)
                updated_count, errors = corrector.apply_metadata_to_flacs(new_metadata)
                
                print(f"\n📊 Results: {updated_count} files updated")
                
                if errors:
                    print(f"❌ Errors: {len(errors)}")
                    for error in errors:
                        print(f"   {error}")
                
                # Rename files if requested
                if args.rename:
                    renamed_count, rename_errors = corrector.rename_files(new_metadata)
                    print(f"📝 Renamed: {renamed_count} files")
                    
                    if rename_errors:
                        for error in rename_errors:
                            print(f"   ❌ {error}")
                
                print("\n🎉 Metadata correction completed!")
                
            except Exception as e:
                print(f"❌ Error applying MBID {args.mbid}: {e}")
                return 1
        
        else:
            # Interactive search and selection
            search_query = args.search
            if not search_query:
                artist = current_metadata.get('artist', '')
                album = current_metadata.get('album', '')
                search_query = f'artist:"{artist}" AND release:"{album}"' if artist and album else album
            
            if not search_query:
                print("❌ No search query available. Use --search or ensure metadata has artist/album info.")
                return 1
            
            print(f"\n🔍 Searching for alternatives...")
            releases = corrector.search_musicbrainz_releases(search_query)
            
            if not releases:
                print("❌ No alternative releases found.")
                print("💡 Try using --search with a different query")
                return 1
            
            # Display options
            corrector.display_release_options(releases, flac_count)
            
            # Let user select
            selected_release = corrector.select_release(releases)
            
            if not selected_release:
                print("Operation cancelled.")
                return 0
            
            # Extract detailed metadata
            new_metadata = corrector.extract_detailed_metadata(selected_release['detailed_info'])
            
            print(f"\n📋 Will apply metadata from: {new_metadata['album']} ({new_metadata['date']})")
            print(f"🎵 Tracks: {len(new_metadata['tracks'])}")
            
            if not args.apply:
                print("\n📋 Preview mode - use --apply to make changes")
                print("💡 Run again with --apply to perform the correction")
                return 0
            
            # Confirm application
            confirm = input("\nApply these changes? (y/n): ").strip().lower()
            if confirm not in ['y', 'yes']:
                print("Operation cancelled.")
                return 0
            
            # Apply changes
            print("\n🚀 Applying metadata corrections...")
            corrector.update_rip_info(new_metadata)
            updated_count, errors = corrector.apply_metadata_to_flacs(new_metadata)
            
            print(f"\n📊 Results: {updated_count} files updated")
            
            if errors:
                print(f"❌ Errors: {len(errors)}")
                for error in errors:
                    print(f"   {error}")
            
            # Rename files if requested
            if args.rename:
                renamed_count, rename_errors = corrector.rename_files(new_metadata)
                print(f"📝 Renamed: {renamed_count} files")
                
                if rename_errors:
                    for error in rename_errors:
                        print(f"   ❌ {error}")
            
            print("\n🎉 Metadata correction completed!")
    
    except Exception as e:
        print(f"❌ Error: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())