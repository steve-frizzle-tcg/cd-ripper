#!/usr/bin/env python3
"""
Individual Track Ripper - Complete any partially ripped album

This tool allows you to rip specific missing tracks from any album without
affecting existing tracks. Useful for:
- Completing albums where some tracks failed to rip
- Re-ripping damaged or corrupted individual tracks
- Adding tracks that were skipped during initial rip

Usage:
    python3 rip_individual_track.py [album_path]
    
If no album_path is provided, you'll be prompted to select from available albums.
"""

import sys
import json
import argparse
from pathlib import Path

# Add parent directory to Python path to import from core
sys.path.insert(0, str(Path(__file__).parent))

from rip_cd import CDRipper
import subprocess

def rip_track_with_recovery(ripper, track_num: int, output_path, cd_device: str) -> bool:
    """Try to rip a problematic track with enhanced error recovery"""
    try:
        print(f"    Using aggressive error correction for track {track_num}...")
        
        temp_wav = ripper.temp_dir / f"track_{track_num:02d}_recovery.wav"
        temp_wav.unlink(missing_ok=True)
        
        # Try more aggressive cdparanoia options
        recovery_options = [
            # Option 1: Reduce overlap and use maximum retries
            ["cdparanoia", "-d", cd_device, "-v", "-o", "1", "-Y", f"{track_num}", str(temp_wav)],
            # Option 2: Force through errors with -Z
            ["cdparanoia", "-d", cd_device, "-Z", "-v", f"{track_num}", str(temp_wav)],
            # Option 3: Skip verification and force output
            ["cdparanoia", "-d", cd_device, "-X", "-v", f"{track_num}", str(temp_wav)]
        ]
        
        for i, cmd in enumerate(recovery_options, 1):
            print(f"    Recovery attempt {i}/3...")
            try:
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=600  # Longer timeout for recovery
                )
                
                if result.returncode == 0 and temp_wav.exists() and temp_wav.stat().st_size > 1000000:  # At least 1MB
                    print(f"    ✅ Recovery successful with method {i}")
                    break
                else:
                    print(f"    ❌ Recovery method {i} failed")
                    temp_wav.unlink(missing_ok=True)
                    
            except subprocess.TimeoutExpired:
                print(f"    ⏰ Recovery method {i} timed out")
                temp_wav.unlink(missing_ok=True)
                continue
        else:
            print("    ❌ All recovery methods failed")
            return False
        
        # Convert to FLAC
        print("    Converting to FLAC...")
        flac_cmd = ["flac", "--best", "--verify", "-f", "-o", str(output_path), str(temp_wav)]
        flac_result = subprocess.run(
            flac_cmd,
            capture_output=True,
            text=True,
            timeout=300
        )
        
        if flac_result.returncode != 0:
            print(f"    ❌ FLAC encoding failed: {flac_result.stderr}")
            return False
        
        # Cleanup
        temp_wav.unlink(missing_ok=True)
        
        if output_path.exists() and output_path.stat().st_size > 100000:  # At least 100KB
            print(f"    ✅ Recovery successful! Created {output_path.stat().st_size} byte FLAC")
            return True
        else:
            print("    ❌ FLAC file too small or missing")
            return False
            
    except Exception as e:
        print(f"    ❌ Recovery failed with error: {e}")
        return False

def find_albums_with_missing_tracks(output_dir: Path) -> list:
    """Find all albums that have missing tracks"""
    incomplete_albums = []
    
    for artist_dir in output_dir.iterdir():
        if not artist_dir.is_dir():
            continue
            
        for album_dir in artist_dir.iterdir():
            if not album_dir.is_dir():
                continue
                
            rip_info_path = album_dir / "rip_info.json"
            if not rip_info_path.exists():
                continue
                
            try:
                with open(rip_info_path, 'r') as f:
                    rip_info = json.load(f)
                
                tracks_ripped = rip_info.get('tracks_ripped', 0)
                total_tracks = rip_info.get('total_tracks', 0)
                
                if tracks_ripped < total_tracks:
                    incomplete_albums.append({
                        'path': album_dir,
                        'artist': rip_info['metadata'].get('artist', 'Unknown'),
                        'album': rip_info['metadata'].get('album', 'Unknown'),
                        'ripped': tracks_ripped,
                        'total': total_tracks,
                        'missing': total_tracks - tracks_ripped
                    })
            except (json.JSONDecodeError, KeyError):
                continue
    
    return incomplete_albums

def select_album(output_dir: Path) -> Path:
    """Allow user to select an album to complete"""
    
    # First, check for incomplete albums
    incomplete_albums = find_albums_with_missing_tracks(output_dir)
    
    if incomplete_albums:
        print("🎵 Albums with missing tracks:")
        print("=" * 60)
        for i, album in enumerate(incomplete_albums, 1):
            print(f"{i:2d}. {album['artist']} - {album['album']}")
            print(f"    Missing: {album['missing']} tracks ({album['ripped']}/{album['total']} complete)")
        
        print("\nOther options:")
        print(f"{len(incomplete_albums) + 1:2d}. Browse all albums")
        print(f"{len(incomplete_albums) + 2:2d}. Enter album path manually")
        
        while True:
            try:
                choice = input(f"\nSelect album (1-{len(incomplete_albums) + 2}): ").strip()
                choice_num = int(choice)
                
                if 1 <= choice_num <= len(incomplete_albums):
                    return incomplete_albums[choice_num - 1]['path']
                elif choice_num == len(incomplete_albums) + 1:
                    return browse_all_albums(output_dir)
                elif choice_num == len(incomplete_albums) + 2:
                    return get_manual_path()
                else:
                    print(f"Please enter a number between 1 and {len(incomplete_albums) + 2}")
            except ValueError:
                print("Please enter a valid number")
    else:
        print("✅ No incomplete albums found!")
        print("Options:")
        print("1. Browse all albums")
        print("2. Enter album path manually")
        
        while True:
            choice = input("Select option (1-2): ").strip()
            if choice == "1":
                return browse_all_albums(output_dir)
            elif choice == "2":
                return get_manual_path()
            else:
                print("Please enter 1 or 2")

def browse_all_albums(output_dir: Path) -> Path:
    """Browse all albums in the output directory"""
    albums = []
    
    for artist_dir in output_dir.iterdir():
        if not artist_dir.is_dir():
            continue
            
        for album_dir in artist_dir.iterdir():
            if not album_dir.is_dir():
                continue
                
            rip_info_path = album_dir / "rip_info.json"
            if rip_info_path.exists():
                try:
                    with open(rip_info_path, 'r') as f:
                        rip_info = json.load(f)
                    
                    albums.append({
                        'path': album_dir,
                        'artist': rip_info['metadata'].get('artist', 'Unknown'),
                        'album': rip_info['metadata'].get('album', 'Unknown'),
                        'ripped': rip_info.get('tracks_ripped', 0),
                        'total': rip_info.get('total_tracks', 0)
                    })
                except (json.JSONDecodeError, KeyError):
                    continue
    
    if not albums:
        print("❌ No albums found with rip_info.json")
        return None
    
    print("\n🎵 All Albums:")
    print("=" * 60)
    for i, album in enumerate(albums, 1):
        status = "✅ Complete" if album['ripped'] == album['total'] else f"⚠️  {album['ripped']}/{album['total']}"
        print(f"{i:2d}. {album['artist']} - {album['album']} ({status})")
    
    while True:
        try:
            choice = input(f"\nSelect album (1-{len(albums)}): ").strip()
            choice_num = int(choice)
            
            if 1 <= choice_num <= len(albums):
                return albums[choice_num - 1]['path']
            else:
                print(f"Please enter a number between 1 and {len(albums)}")
        except ValueError:
            print("Please enter a valid number")

def get_manual_path() -> Path:
    """Get album path manually from user"""
    while True:
        path_str = input("\nEnter full path to album directory: ").strip()
        album_path = Path(path_str)
        
        if not album_path.exists():
            print(f"❌ Directory not found: {album_path}")
            continue
            
        rip_info_path = album_path / "rip_info.json"
        if not rip_info_path.exists():
            print(f"❌ No rip_info.json found in: {album_path}")
            print("This doesn't appear to be a ripped album directory.")
            continue
            
        return album_path

def rip_individual_tracks(album_path: Path = None):
    """Rip individual tracks to complete an existing album"""
    
    output_dir = Path.home() / "cd_ripping" / "output"
    
    if album_path is None:
        album_path = select_album(output_dir)
        if album_path is None:
            return False
    
    if not album_path.exists():
        print(f"❌ Album directory not found: {album_path}")
        return False
    
    # Load existing metadata
    rip_info_path = album_path / "rip_info.json"
    if not rip_info_path.exists():
        print(f"❌ rip_info.json not found: {rip_info_path}")
        return False
    
    with open(rip_info_path, 'r') as f:
        rip_info = json.load(f)
    
    metadata = rip_info['metadata']
    tracks = metadata.get('tracks', [])
    
    artist_name = metadata.get('artist', 'Unknown Artist')
    album_name = metadata.get('album', 'Unknown Album')
    
    print(f"🎵 Individual Track Ripper for {artist_name} - {album_name}")
    print("=" * 80)
    print(f"Album has {len(tracks)} total tracks")
    print(f"Currently ripped: {rip_info['tracks_ripped']}/{rip_info['total_tracks']}")
    print(f"Album directory: {album_path}")
    print()
    
    # Show missing tracks
    existing_files = sorted(album_path.glob("01-*.flac"))
    existing_track_nums = []
    
    for file in existing_files:
        import re
        match = re.search(r'01-(\d+)\.', file.name)
        if match:
            existing_track_nums.append(int(match.group(1)))
    
    missing_tracks = []
    for i, track in enumerate(tracks, 1):
        if i not in existing_track_nums:
            missing_tracks.append((i, track['title']))
    
    if not missing_tracks:
        print("✅ All tracks are already ripped!")
        return True
        
    print("Missing tracks:")
    for track_num, title in missing_tracks:
        print(f"  Track {track_num:2d}: {title}")
    
    print()
    track_to_rip = input("Enter track number to rip (or 'all' for all missing, 'q' to quit): ").strip()
    
    if track_to_rip.lower() == 'q':
        print("Operation cancelled.")
        return False
    elif track_to_rip.lower() == 'all':
        tracks_to_rip = [track_num for track_num, _ in missing_tracks]
        print(f"Will rip {len(tracks_to_rip)} missing tracks: {', '.join(map(str, tracks_to_rip))}")
    else:
        try:
            track_num = int(track_to_rip)
            if track_num not in [t[0] for t in missing_tracks]:
                print(f"❌ Track {track_num} is not missing or doesn't exist")
                return False
            tracks_to_rip = [track_num]
            print(f"Will rip track {track_num}: {tracks[track_num-1]['title']}")
        except ValueError:
            print("❌ Invalid input. Enter a track number, 'all', or 'q'")
            return False
    
    # Initialize ripper
    ripper = CDRipper()
    
    # Check CD and get device
    if not ripper.check_cd_presence():
        print("❌ No CD found in drive")
        return False
    
    cd_device = ripper.find_cd_device()
    print(f"📀 Using CD device: {cd_device}")
    
    # Rip the selected tracks
    successful_rips = 0
    
    for track_num in tracks_to_rip:
        track_info = tracks[track_num - 1]  # Convert to 0-based index
        track_title = track_info['title']
        
        print(f"\n🎵 Ripping Track {track_num}: {track_title}")
        
        # Create temporary filename for ripping
        temp_flac = album_path / f"Track_{track_num:02d}.flac"
        
        # Try ripping the track with enhanced error recovery
        print("  Attempting rip with standard settings...")
        if ripper.rip_track(track_num, temp_flac, cd_device):
            success = True
        else:
            print("  Standard rip failed, trying with error recovery...")
            success = rip_track_with_recovery(ripper, track_num, temp_flac, cd_device)
        
        if success:
            print(f"✅ Successfully ripped track {track_num}")
            
            # Rename to proper format
            safe_title = track_title.replace('/', '_').replace('\\', '_').replace(':', '_')
            safe_title = safe_title.replace('?', '').replace('*', '').replace('"', "'")
            safe_title = safe_title.replace('<', '').replace('>', '').replace('|', '_')
            
            final_filename = f"01-{track_num:02d}. {safe_title}.flac"
            final_path = album_path / final_filename
            
            # Rename the file
            temp_flac.rename(final_path)
            print(f"📝 Renamed to: {final_filename}")
            
            # Add metadata to the new track
            from mutagen.flac import FLAC
            
            try:
                audio = FLAC(str(final_path))
                
                # Basic metadata
                audio['ALBUM'] = metadata['album']
                audio['DATE'] = metadata['date']
                audio['ARTIST'] = metadata['artist']
                audio['TITLE'] = track_title
                audio['TRACKNUMBER'] = f"{track_num:02d}"
                audio['DISCNUMBER'] = "1"
                audio['TOTALDISCS'] = "1"
                audio['TOTALTRACKS'] = str(len(tracks))
                
                if metadata.get('mbid') and metadata['mbid'] != 'user-entered':
                    audio['MUSICBRAINZ_ALBUMID'] = metadata['mbid']
                
                # Add cover art if it exists
                cover_path = album_path / "cover.jpg"
                if cover_path.exists():
                    with open(cover_path, 'rb') as f:
                        image_data = f.read()
                    
                    from mutagen.flac import Picture
                    picture = Picture()
                    picture.type = 3  # Cover (front)
                    picture.mime = 'image/jpeg'
                    picture.data = image_data
                    audio.add_picture(picture)
                
                audio.save()
                print(f"✅ Added metadata to track {track_num}")
                successful_rips += 1
                
            except Exception as e:
                print(f"❌ Failed to add metadata to track {track_num}: {e}")
                
        else:
            print(f"❌ Failed to rip track {track_num}")
    
    # Update rip_info.json
    if successful_rips > 0:
        rip_info['tracks_ripped'] += successful_rips
        
        with open(rip_info_path, 'w') as f:
            json.dump(rip_info, f, indent=2)
        
        print(f"\n✅ Successfully ripped {successful_rips} track(s)")
        print(f"📊 Album now has {rip_info['tracks_ripped']}/{rip_info['total_tracks']} tracks")
        
        if rip_info['tracks_ripped'] == rip_info['total_tracks']:
            print("🎉 Album is now complete!")
    
    return successful_rips > 0

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Complete partially ripped albums by adding missing tracks",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python3 rip_individual_track.py
        # Interactive mode - select from incomplete albums
    
    python3 rip_individual_track.py "/path/to/album"
        # Direct mode - specify album path
    
    python3 rip_individual_track.py --list-incomplete
        # List all incomplete albums and exit
        """
    )
    
    parser.add_argument(
        'album_path', 
        nargs='?', 
        help='Path to album directory (optional - will prompt if not provided)'
    )
    parser.add_argument(
        '--list-incomplete', 
        action='store_true',
        help='List all incomplete albums and exit'
    )
    parser.add_argument(
        '--list-all', 
        action='store_true',
        help='List all albums with completion status and exit'
    )
    
    args = parser.parse_args()
    
    output_dir = Path.home() / "cd_ripping" / "output"
    
    if args.list_incomplete:
        incomplete_albums = find_albums_with_missing_tracks(output_dir)
        if incomplete_albums:
            print("🎵 Albums with missing tracks:")
            print("=" * 60)
            for album in incomplete_albums:
                print(f"• {album['artist']} - {album['album']}")
                print(f"  Missing: {album['missing']} tracks ({album['ripped']}/{album['total']} complete)")
                print(f"  Path: {album['path']}")
                print()
        else:
            print("✅ All albums are complete!")
        return
    
    if args.list_all:
        albums = []
        
        for artist_dir in output_dir.iterdir():
            if not artist_dir.is_dir():
                continue
                
            for album_dir in artist_dir.iterdir():
                if not album_dir.is_dir():
                    continue
                    
                rip_info_path = album_dir / "rip_info.json"
                if rip_info_path.exists():
                    try:
                        with open(rip_info_path, 'r') as f:
                            rip_info = json.load(f)
                        
                        albums.append({
                            'artist': rip_info['metadata'].get('artist', 'Unknown'),
                            'album': rip_info['metadata'].get('album', 'Unknown'),
                            'ripped': rip_info.get('tracks_ripped', 0),
                            'total': rip_info.get('total_tracks', 0)
                        })
                    except (json.JSONDecodeError, KeyError):
                        continue
        
        if albums:
            albums.sort(key=lambda x: (x['artist'].lower(), x['album'].lower()))
            print(f"🎵 All Albums ({len(albums)} total):")
            print("=" * 80)
            for album in albums:
                status = "✅ Complete" if album['ripped'] == album['total'] else f"⚠️  {album['ripped']}/{album['total']}"
                print(f"{album['artist']} - {album['album']} ({status})")
        else:
            print("❌ No albums found.")
        return
    
    album_path = None
    if args.album_path:
        album_path = Path(args.album_path)
        if not album_path.exists():
            print(f"❌ Album directory not found: {album_path}")
            return
    
    print("🎵 Individual Track Ripper")
    print("=" * 50)
    print("This tool completes partially ripped albums by adding missing tracks.")
    print()
    
    if album_path is None:
        print("Please select an album to complete:")
    else:
        print(f"Album: {album_path}")
        
    print("\nInsert the CD and press Enter when ready...")
    input()
    
    success = rip_individual_tracks(album_path)
    
    if success:
        print("\n✅ Individual track ripping completed!")
    else:
        print("\n❌ Individual track ripping failed.")

if __name__ == "__main__":
    main()
