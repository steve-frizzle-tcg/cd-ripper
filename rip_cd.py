#!/usr/bin/env python3
"""
CD Ripping Script - Part 1 (Simplified)
Rips CDs to FLAC first, then adds metadata
"""

import os
import sys
import subprocess
import time
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import musicbrainzngs
import requests
from mutagen.flac import FLAC

# Configure logging
def setup_logging():
    log_dir = Path.home() / "cd_ripping" / "logs"
    log_dir.mkdir(exist_ok=True)
    
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    log_file = log_dir / f"rip_cd_{timestamp}.log"
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler(sys.stdout)
        ]
    )
    return logging.getLogger(__name__)

# Configure MusicBrainz
musicbrainzngs.set_useragent(
    "CD-Ripper-Script",
    "1.0",
    "https://github.com/steve-frizzle-tcg/cd-ripper"
)

class CDRipperError(Exception):
    """Custom exception for CD ripping errors"""
    pass

class CDRipper:
    def __init__(self, temp_dir: str = None, output_dir: str = None):
        self.logger = setup_logging()
        self.home = Path.home()
        self.temp_dir = Path(temp_dir) if temp_dir else self.home / "cd_ripping" / "temp"
        self.output_dir = Path(output_dir) if output_dir else self.home / "cd_ripping" / "output"
        self.covers_dir = self.home / "cd_ripping" / "covers"
        
        # Ensure directories exist
        for dir_path in [self.temp_dir, self.output_dir, self.covers_dir]:
            dir_path.mkdir(parents=True, exist_ok=True)

    def check_cd_presence(self) -> bool:
        """Check if CD is present in drive"""
        try:
            result = subprocess.run(
                ["cdparanoia", "-Q"],
                capture_output=True,
                text=True,
                timeout=10
            )
            return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError) as e:
            self.logger.error(f"Error checking CD presence: {e}")
            return False

    def get_track_count(self) -> int:
        """Get number of audio tracks on CD"""
        try:
            result = subprocess.run(
                ["cdparanoia", "-Q"],
                capture_output=True,
                text=True,
                check=True
            )
            
            track_count = 0
            for line in result.stderr.split('\n'):
                if line.strip().startswith(tuple('123456789')) and '.' in line and '[' in line:
                    track_count += 1
            
            self.logger.info(f"Found {track_count} tracks on CD")
            return track_count
            
        except subprocess.CalledProcessError as e:
            raise CDRipperError(f"Failed to get track count: {e}")

    def find_cd_device(self) -> str:
        """Find the CD device path"""
        possible_devices = ["/dev/cdrom", "/dev/sr0", "/dev/sr1"]
        
        for device in possible_devices:
            if os.path.exists(device):
                self.logger.info(f"Found CD device: {device}")
                return device
        
        self.logger.warning("No CD device found, using /dev/cdrom")
        return "/dev/cdrom"

    def rip_track(self, track_num: int, output_path: Path, cd_device: str) -> bool:
        """Rip single track using cdparanoia"""
        try:
            self.logger.info(f"Ripping track {track_num}...")
            
            temp_wav = self.temp_dir / f"track_{track_num:02d}.wav"
            temp_wav.unlink(missing_ok=True)
            
            # Rip to WAV
            cmd = ["cdparanoia", "-d", cd_device, f"{track_num}", str(temp_wav)]
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300
            )
            
            if result.returncode != 0:
                self.logger.error(f"cdparanoia failed for track {track_num}")
                self.logger.error(f"Command: {' '.join(cmd)}")
                self.logger.error(f"Error: {result.stderr}")
                return False
            
            # Verify WAV file
            if not temp_wav.exists() or temp_wav.stat().st_size == 0:
                self.logger.error(f"WAV file not created or empty for track {track_num}")
                return False
                
            wav_size = temp_wav.stat().st_size
            self.logger.info(f"WAV created: {wav_size} bytes")
            
            # Convert to FLAC
            flac_cmd = ["flac", "--best", "--verify", "-f", "-o", str(output_path), str(temp_wav)]
            flac_result = subprocess.run(
                flac_cmd,
                capture_output=True,
                text=True,
                timeout=300
            )
            
            if flac_result.returncode != 0:
                self.logger.error(f"FLAC encoding failed for track {track_num}")
                self.logger.error(f"Command: {' '.join(flac_cmd)}")
                self.logger.error(f"Error: {flac_result.stderr}")
                return False
            
            # Verify FLAC file
            if not output_path.exists() or output_path.stat().st_size == 0:
                self.logger.error(f"FLAC file not created or empty for track {track_num}")
                return False
                
            flac_size = output_path.stat().st_size
            self.logger.info(f"FLAC created: {flac_size} bytes")
            
            # Cleanup
            temp_wav.unlink(missing_ok=True)
            
            self.logger.info(f"Successfully ripped track {track_num}")
            return True
            
        except subprocess.TimeoutExpired:
            self.logger.error(f"Timeout ripping track {track_num}")
            return False
        except Exception as e:
            self.logger.error(f"Error ripping track {track_num}: {e}")
            return False

    def rip_all_tracks(self, track_count: int, album_dir: Path, cd_device: str) -> int:
        """Rip all tracks from CD"""
        successful_tracks = 0
        
        self.logger.info(f"Starting to rip {track_count} tracks...")
        
        for track_num in range(1, track_count + 1):
            flac_filename = f"Track_{track_num:02d}.flac"
            flac_path = album_dir / flac_filename
            
            self.logger.info(f"Processing track {track_num}/{track_count}")
            
            if self.rip_track(track_num, flac_path, cd_device):
                successful_tracks += 1
                self.logger.info(f"Track {track_num} completed successfully")
            else:
                self.logger.error(f"Failed to rip track {track_num}")
                # Continue with other tracks
        
        return successful_tracks

    def get_user_metadata(self) -> Dict:
        """Get basic metadata from user"""
        print("\n=== Album Information ===")
        print("Please enter the album information (will be refined later with MusicBrainz lookup):")
        artist = input("Artist name: ").strip() or "Unknown Artist"
        album = input("Album name: ").strip() or "Unknown Album"
        year = input("Year (optional): ").strip() or "Unknown"
        
        return {
            'artist': artist,
            'album': album,
            'date': year,
            'mbid': 'user-entered',
            'method': 'manual'
        }

    def search_musicbrainz_enhanced(self, artist: str, album: str, track_count: int) -> Optional[Dict]:
        """Enhanced MusicBrainz search with track information"""
        try:
            self.logger.info(f"Searching MusicBrainz for: {artist} - {album} ({track_count} tracks)")
            
            # Search for releases
            query = f'artist:"{artist}" AND release:"{album}"'
            releases = musicbrainzngs.search_releases(query=query, limit=10)
            
            if not releases.get('release-list'):
                self.logger.info("No exact matches found, trying broader search...")
                # Try broader search without quotes
                query = f'artist:{artist} AND release:{album}'
                releases = musicbrainzngs.search_releases(query=query, limit=10)
            
            if not releases.get('release-list'):
                return None
            
            # Find release that matches our track count
            best_release = None
            for release in releases['release-list']:
                try:
                    # Get detailed release info including tracks
                    release_detail = musicbrainzngs.get_release_by_id(
                        release['id'], 
                        includes=['recordings', 'artist-credits']
                    )
                    
                    medium_list = release_detail['release'].get('medium-list', [])
                    if medium_list:
                        release_track_count = sum(len(medium.get('track-list', [])) for medium in medium_list)
                        
                        if release_track_count == track_count:
                            best_release = release_detail['release']
                            break
                        elif not best_release:  # Keep first match as fallback
                            best_release = release_detail['release']
                            
                except Exception as e:
                    self.logger.debug(f"Error getting release details for {release['id']}: {e}")
                    continue
            
            if not best_release:
                return None
            
            # Extract track information
            tracks = []
            medium_list = best_release.get('medium-list', [])
            for medium in medium_list:
                for track in medium.get('track-list', []):
                    recording = track.get('recording', {})
                    tracks.append({
                        'title': recording.get('title', f"Track {len(tracks) + 1:02d}"),
                        'length': track.get('length')
                    })
            
            # Get proper artist name from artist-credits
            artist_name = artist  # fallback
            if 'artist-credit' in best_release:
                artist_credit = best_release['artist-credit']
                if artist_credit and len(artist_credit) > 0:
                    artist_name = artist_credit[0].get('artist', {}).get('name', artist)
            
            return {
                'artist': artist_name,
                'album': best_release.get('title', album),
                'date': best_release.get('date', 'Unknown'),
                'mbid': best_release['id'],
                'tracks': tracks,
                'method': 'musicbrainz-enhanced'
            }
            
        except Exception as e:
            self.logger.warning(f"Enhanced MusicBrainz search failed: {e}")
            return None

    def search_musicbrainz_simple(self, artist: str, album: str) -> Optional[Dict]:
        """Simple MusicBrainz search with basic error handling"""
        try:
            self.logger.info(f"Searching MusicBrainz for: {artist} - {album}")
            
            query = f'artist:"{artist}" AND release:"{album}"'
            releases = musicbrainzngs.search_releases(query=query, limit=5)
            
            if not releases.get('release-list'):
                return None
            
            # Return first match
            release = releases['release-list'][0]
            return {
                'artist': artist,
                'album': album,
                'date': release.get('date', 'Unknown'),
                'mbid': release['id'],
                'method': 'musicbrainz-simple'
            }
            
        except Exception as e:
            self.logger.warning(f"MusicBrainz search failed: {e}")
            return None

    def download_cover_art_simple(self, mbid: str, artist: str, album: str) -> Optional[str]:
        """Simple cover art download with error handling"""
        try:
            url = f"https://coverartarchive.org/release/{mbid}/front"
            response = requests.get(url, timeout=30, stream=True)
            response.raise_for_status()
            
            # Save cover with safe filename (replace only problematic characters)
            safe_filename = f"{artist}_{album}".replace('/', '_').replace('\\', '_').replace(':', '_')
            safe_filename = safe_filename.replace('?', '').replace('*', '').replace('"', "'")
            safe_filename = safe_filename.replace('<', '').replace('>', '').replace('|', '_')
            cover_path = self.covers_dir / f"{safe_filename}.jpg"
            
            with open(cover_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            self.logger.info(f"Cover art downloaded: {cover_path}")
            return str(cover_path)
            
        except Exception as e:
            self.logger.warning(f"Cover art download failed: {e}")
            return None

    def reorganize_album_directory(self, old_album_dir: Path, new_metadata: Dict) -> Path:
        """Reorganize album directory with correct artist and album names"""
        try:
            # Create new directory structure: output > artist > album
            # Only replace forward slashes to avoid path issues, keep other characters including spaces
            safe_artist = new_metadata['artist'].replace('/', '_')
            safe_album = new_metadata['album'].replace('/', '_')
            
            # Create nested directory structure
            artist_dir = self.output_dir / safe_artist
            new_album_dir = artist_dir / safe_album
            
            if old_album_dir == new_album_dir:
                return old_album_dir  # No change needed
            
            # Create new directory structure
            new_album_dir.mkdir(parents=True, exist_ok=True)
            
            # Move all files from old to new directory
            for file_path in old_album_dir.iterdir():
                if file_path.is_file():
                    new_file_path = new_album_dir / file_path.name
                    file_path.rename(new_file_path)
                    self.logger.info(f"Moved {file_path.name} to new directory")
            
            # Remove old directory if empty
            try:
                old_album_dir.rmdir()
                self.logger.info(f"Removed old directory: {old_album_dir}")
            except OSError:
                self.logger.warning(f"Could not remove old directory: {old_album_dir}")
            
            return new_album_dir
            
        except Exception as e:
            self.logger.error(f"Failed to reorganize directory: {e}")
            return old_album_dir

    def rename_track_files(self, album_dir: Path, metadata: Dict) -> List[Path]:
        """Rename track files with proper names from metadata"""
        try:
            flac_files = sorted(album_dir.glob("Track_*.flac"))
            tracks = metadata.get('tracks', [])
            renamed_files = []
            
            for i, flac_path in enumerate(flac_files):
                try:
                    if i < len(tracks):
                        # Use MusicBrainz track title
                        track_title = tracks[i]['title']
                    else:
                        # Fallback to generic name
                        track_title = f"Track {i+1:02d}"
                    
                    # Sanitize filename
                    safe_title = track_title.replace('/', '_').replace('\\', '_').replace(':', '_')
                    safe_title = safe_title.replace('?', '').replace('*', '').replace('"', "'")
                    safe_title = safe_title.replace('<', '').replace('>', '').replace('|', '_')
                    
                    new_filename = f"{i+1:02d}. {safe_title}.flac"
                    new_path = album_dir / new_filename
                    
                    if flac_path != new_path:
                        flac_path.rename(new_path)
                        self.logger.info(f"Renamed {flac_path.name} to {new_filename}")
                        renamed_files.append(new_path)
                    else:
                        renamed_files.append(flac_path)
                        
                except Exception as e:
                    self.logger.error(f"Failed to rename {flac_path.name}: {e}")
                    renamed_files.append(flac_path)
            
            return renamed_files
            
        except Exception as e:
            self.logger.error(f"Failed to rename track files: {e}")
            return sorted(album_dir.glob("*.flac"))

    def add_enhanced_metadata(self, flac_files: List[Path], metadata: Dict, cover_path: Optional[str] = None):
        """Add enhanced metadata to all FLAC files using MusicBrainz data"""
        try:
            self.logger.info("Adding enhanced metadata to FLAC files...")
            
            total_tracks = len(flac_files)
            tracks = metadata.get('tracks', [])
            
            for i, flac_path in enumerate(flac_files):
                try:
                    audio = FLAC(str(flac_path))
                    
                    # Basic metadata
                    audio['ARTIST'] = metadata['artist']
                    audio['ALBUM'] = metadata['album']
                    audio['DATE'] = metadata['date']
                    audio['TRACKNUMBER'] = str(i + 1)
                    audio['TOTALTRACKS'] = str(total_tracks)
                    
                    # Track title from MusicBrainz or fallback
                    if i < len(tracks):
                        audio['TITLE'] = tracks[i]['title']
                    else:
                        audio['TITLE'] = f"Track {i+1:02d}"
                    
                    if metadata.get('mbid') and metadata['mbid'] != 'user-entered':
                        audio['MUSICBRAINZ_ALBUMID'] = metadata['mbid']
                    
                    # Add cover art if available
                    if cover_path and os.path.exists(cover_path):
                        with open(cover_path, 'rb') as f:
                            image_data = f.read()
                        
                        from mutagen.flac import Picture
                        picture = Picture()
                        picture.type = 3  # Cover (front)
                        picture.mime = 'image/jpeg'
                        picture.data = image_data
                        audio.add_picture(picture)
                    
                    audio.save()
                    self.logger.info(f"Enhanced metadata added to {flac_path.name}")
                    
                except Exception as e:
                    self.logger.error(f"Failed to add enhanced metadata to {flac_path.name}: {e}")
                    
        except Exception as e:
            self.logger.error(f"Enhanced metadata processing failed: {e}")

    def add_basic_metadata(self, flac_files: List[Path], metadata: Dict, cover_path: Optional[str] = None):
        """Add basic metadata to all FLAC files"""
        try:
            self.logger.info("Adding metadata to FLAC files...")
            
            total_tracks = len(flac_files)
            
            for i, flac_path in enumerate(flac_files, 1):
                try:
                    audio = FLAC(str(flac_path))
                    
                    # Basic metadata
                    audio['ARTIST'] = metadata['artist']
                    audio['ALBUM'] = metadata['album']
                    audio['DATE'] = metadata['date']
                    audio['TRACKNUMBER'] = str(i)
                    audio['TOTALTRACKS'] = str(total_tracks)
                    
                    # Add track title (user can rename later)
                    track_title = input(f"Enter title for track {i} (or press Enter for 'Track {i:02d}'): ").strip()
                    audio['TITLE'] = track_title or f"Track {i:02d}"
                    
                    if metadata.get('mbid') and metadata['mbid'] != 'user-entered':
                        audio['MUSICBRAINZ_ALBUMID'] = metadata['mbid']
                    
                    # Add cover art if available
                    if cover_path and os.path.exists(cover_path):
                        with open(cover_path, 'rb') as f:
                            image_data = f.read()
                        
                        from mutagen.flac import Picture
                        picture = Picture()
                        picture.type = 3  # Cover (front)
                        picture.mime = 'image/jpeg'
                        picture.data = image_data
                        audio.add_picture(picture)
                    
                    audio.save()
                    self.logger.info(f"Metadata added to {flac_path.name}")
                    
                except Exception as e:
                    self.logger.error(f"Failed to add metadata to {flac_path.name}: {e}")
                    
        except Exception as e:
            self.logger.error(f"Metadata processing failed: {e}")

    def rip_cd(self) -> bool:
        """Main CD ripping process - simplified approach"""
        try:
            self.logger.info("=== Starting CD Ripping Process ===")
            
            # Check for CD
            if not self.check_cd_presence():
                raise CDRipperError("No CD found in drive")
            
            # Find device and get track count
            cd_device = self.find_cd_device()
            track_count = self.get_track_count()
            
            if track_count == 0:
                raise CDRipperError("No audio tracks found on CD")
            
            # Get basic info from user
            metadata = self.get_user_metadata()
            
            # Create album directory using nested structure: output > artist > album
            safe_artist = metadata['artist'].replace('/', '_')
            safe_album = metadata['album'].replace('/', '_')
            
            artist_dir = self.output_dir / safe_artist
            album_dir = artist_dir / safe_album
            album_dir.mkdir(parents=True, exist_ok=True)
            
            self.logger.info(f"Album directory: {album_dir}")
            
            # STEP 1: Rip all tracks first (most important part)
            self.logger.info("=== STEP 1: Ripping Tracks ===")
            successful_tracks = self.rip_all_tracks(track_count, album_dir, cd_device)
            
            if successful_tracks == 0:
                raise CDRipperError("No tracks were successfully ripped")
            
            self.logger.info(f"Successfully ripped {successful_tracks}/{track_count} tracks")
            
            # STEP 2: Try to enhance metadata (optional)
            self.logger.info("=== STEP 2: Adding Metadata ===")
            
            # Try enhanced MusicBrainz lookup first (with track info)
            mb_metadata = self.search_musicbrainz_enhanced(metadata['artist'], metadata['album'], track_count)
            if not mb_metadata:
                # Fallback to simple search
                mb_metadata = self.search_musicbrainz_simple(metadata['artist'], metadata['album'])
            
            if mb_metadata:
                metadata.update(mb_metadata)
                self.logger.info(f"Enhanced metadata from MusicBrainz: {metadata['method']}")
                
                # Reorganize directory with correct artist/album names
                album_dir = self.reorganize_album_directory(album_dir, metadata)
            
            # Try to download cover art (optional)
            cover_path = None
            if metadata.get('mbid') and metadata['mbid'] != 'user-entered':
                cover_path = self.download_cover_art_simple(
                    metadata['mbid'], 
                    metadata['artist'], 
                    metadata['album']
                )
            
            # Get FLAC files and add metadata
            flac_files = sorted(album_dir.glob("Track_*.flac"))
            if flac_files:
                if metadata.get('tracks'):
                    # Enhanced metadata with track names
                    flac_files = self.rename_track_files(album_dir, metadata)
                    self.add_enhanced_metadata(flac_files, metadata, cover_path)
                else:
                    # Basic metadata - ask user for track names
                    self.add_basic_metadata(flac_files, metadata, cover_path)
            
            # Save metadata file for reference
            metadata_file = album_dir / "rip_info.json"
            rip_info = {
                'metadata': metadata,
                'rip_date': time.strftime("%Y-%m-%d %H:%M:%S"),
                'tracks_ripped': successful_tracks,
                'total_tracks': track_count,
                'cover_art': cover_path,
                'device': cd_device
            }
            
            with open(metadata_file, 'w') as f:
                json.dump(rip_info, f, indent=2)
            
            self.logger.info("=== Ripping Process Complete ===")
            self.logger.info(f"Location: {album_dir}")
            self.logger.info(f"Tracks: {successful_tracks}/{track_count}")
            
            # Eject CD
            try:
                subprocess.run(["eject"], check=False)
                self.logger.info("CD ejected")
            except:
                pass
            
            return successful_tracks > 0
            
        except Exception as e:
            self.logger.error(f"CD ripping failed: {e}")
            return False

def main():
    """Main entry point"""
    ripper = CDRipper()
    
    print("=== CD Ripper - Part 1 (Simplified) ===")
    print("This script will:")
    print("1. Rip all tracks to FLAC files")
    print("2. Add basic metadata")
    print("3. Optionally download cover art")
    print()
    print("Insert CD and press Enter to start...")
    input()
    
    success = ripper.rip_cd()
    
    if success:
        print("\n✅ CD ripping completed successfully!")
        print("You can now:")
        print("- Play the FLAC files")
        print("- Edit metadata later if needed")
        print("- Run Part 2 to upload to S3")
        return 0
    else:
        print("\n❌ CD ripping failed. Check logs for details.")
        return 1

if __name__ == "__main__":
    sys.exit(main())