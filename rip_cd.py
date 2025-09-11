#!/usr/bin/env python3
"""
CD Ripping Script - Part 1
Rips CDs to FLAC with metadata enrichment via MusicBrainz API
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
from PIL import Image

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
    "https://github.com/steve-frizzle-tcg/cd-ripper"  # Replace with actual contact
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
        except subprocess.TimeoutExpired:
            self.logger.error("Timeout checking for CD presence")
            return False
        except Exception as e:
            self.logger.error(f"Error checking CD presence: {e}")
            return False

    def get_cd_info(self) -> Tuple[str, List[int]]:
        """Get CD info including disc ID and track lengths"""
        try:
            self.logger.info("Getting CD information...")
            result = subprocess.run(
                ["cdparanoia", "-Q"],
                capture_output=True,
                text=True,
                check=True
            )
            
            lines = result.stderr.split('\n')
            track_info = []
            disc_id = None
            
            for line in lines:
                if "TOTAL" in line and "disc" in line:
                    # Extract basic disc info for MusicBrainz lookup
                    parts = line.strip().split()
                    if len(parts) >= 3:
                        total_time = parts[1]
                        self.logger.info(f"Total disc time: {total_time}")
                
                if line.strip().startswith(tuple('123456789')):
                    # Track line format: "  1.   [00:02.47]  4372 [  0:58.48]  audio"
                    parts = line.strip().split()
                    if len(parts) >= 4:
                        track_num = int(parts[0].rstrip('.'))
                        # Extract length in sectors (rough estimate)
                        length_str = parts[1].strip('[]')
                        track_info.append((track_num, length_str))
            
            self.logger.info(f"Found {len(track_info)} tracks")
            return disc_id, track_info
            
        except subprocess.CalledProcessError as e:
            raise CDRipperError(f"Failed to get CD info: {e}")

    def lookup_musicbrainz(self, track_count: int) -> Optional[Dict]:
        """Lookup CD metadata using MusicBrainz"""
        try:
            self.logger.info("Looking up CD metadata in MusicBrainz...")
            
            # For demonstration, we'll search by track count
            # In practice, you'd use disc ID or TOC for accurate matching
            releases = musicbrainzngs.search_releases(
                query=f'tracks:{track_count}',
                limit=10
            )
            
            if not releases.get('release-list'):
                self.logger.warning("No releases found in MusicBrainz")
                return None
            
            # Take the first result (in practice, you might want user selection)
            release = releases['release-list'][0]
            
            # Get detailed release info
            detailed_release = musicbrainzngs.get_release_by_id(
                release['id'],
                includes=['artist-credits', 'recordings', 'media']
            )
            
            release_info = detailed_release['release']
            
            metadata = {
                'album': release_info.get('title', 'Unknown Album'),
                'artist': release_info['artist-credit'][0]['artist']['name'] if release_info.get('artist-credit') else 'Unknown Artist',
                'date': release_info.get('date', 'Unknown'),
                'mbid': release_info['id'],
                'tracks': []
            }
            
            # Extract track information
            if 'media' in release_info:
                for medium in release_info['media']:
                    for track in medium.get('track-list', []):
                        track_info = {
                            'number': int(track['position']),
                            'title': track['recording']['title'],
                            'length': track.get('length')
                        }
                        metadata['tracks'].append(track_info)
            
            self.logger.info(f"Found metadata for: {metadata['artist']} - {metadata['album']}")
            return metadata
            
        except Exception as e:
            self.logger.error(f"MusicBrainz lookup failed: {e}")
            return None

    def download_cover_art(self, mbid: str, album: str, artist: str) -> Optional[str]:
        """Download cover art from Cover Art Archive"""
        try:
            self.logger.info("Downloading cover art...")
            
            # Cover Art Archive URL
            url = f"https://coverartarchive.org/release/{mbid}/front"
            
            response = requests.get(url, timeout=30, stream=True)
            response.raise_for_status()
            
            # Determine file extension from content type
            content_type = response.headers.get('content-type', '')
            if 'jpeg' in content_type:
                ext = '.jpg'
            elif 'png' in content_type:
                ext = '.png'
            else:
                ext = '.jpg'  # default
            
            # Save cover image
            safe_filename = f"{artist}_{album}".replace('/', '_').replace(' ', '_')
            cover_path = self.covers_dir / f"{safe_filename}{ext}"
            
            with open(cover_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            self.logger.info(f"Cover art saved to: {cover_path}")
            return str(cover_path)
            
        except Exception as e:
            self.logger.error(f"Failed to download cover art: {e}")
            return None

    def rip_track(self, track_num: int, output_path: Path) -> bool:
        """Rip single track using cdparanoia"""
        try:
            self.logger.info(f"Ripping track {track_num}...")
            
            temp_wav = self.temp_dir / f"track_{track_num:02d}.wav"
            
            # Rip to WAV using cdparanoia
            result = subprocess.run([
                "cdparanoia",
                "-d", "/dev/cdrom",  # Adjust device path if needed
                f"{track_num}",
                str(temp_wav)
            ], capture_output=True, text=True)
            
            if result.returncode != 0:
                self.logger.error(f"cdparanoia failed for track {track_num}: {result.stderr}")
                return False
            
            # Convert WAV to FLAC
            flac_result = subprocess.run([
                "flac",
                "--best",  # Maximum compression
                "--verify",  # Verify encoding
                "-o", str(output_path),
                str(temp_wav)
            ], capture_output=True, text=True)
            
            if flac_result.returncode != 0:
                self.logger.error(f"FLAC encoding failed for track {track_num}: {flac_result.stderr}")
                return False
            
            # Clean up temp WAV file
            temp_wav.unlink(missing_ok=True)
            
            self.logger.info(f"Successfully ripped track {track_num}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error ripping track {track_num}: {e}")
            return False

    def add_metadata(self, flac_path: Path, metadata: Dict, track_info: Dict, cover_path: Optional[str] = None):
        """Add metadata to FLAC file"""
        try:
            self.logger.info(f"Adding metadata to {flac_path.name}...")
            
            audio = FLAC(str(flac_path))
            
            # Basic metadata
            audio['TITLE'] = track_info['title']
            audio['ARTIST'] = metadata['artist']
            audio['ALBUM'] = metadata['album']
            audio['DATE'] = metadata['date']
            audio['TRACKNUMBER'] = str(track_info['number'])
            audio['TOTALTRACKS'] = str(len(metadata['tracks']))
            audio['MUSICBRAINZ_ALBUMID'] = metadata['mbid']
            
            # Add cover art if available
            if cover_path and os.path.exists(cover_path):
                with open(cover_path, 'rb') as f:
                    image_data = f.read()
                
                # Create FLAC picture block
                from mutagen.flac import Picture
                picture = Picture()
                picture.type = 3  # Cover (front)
                picture.mime = 'image/jpeg' if cover_path.endswith('.jpg') else 'image/png'
                picture.data = image_data
                
                audio.add_picture(picture)
            
            audio.save()
            self.logger.info(f"Metadata added to {flac_path.name}")
            
        except Exception as e:
            self.logger.error(f"Failed to add metadata to {flac_path.name}: {e}")

    def rip_cd(self) -> bool:
        """Main CD ripping process"""
        try:
            self.logger.info("Starting CD ripping process...")
            
            # Check for CD
            if not self.check_cd_presence():
                raise CDRipperError("No CD found in drive")
            
            # Get CD information
            disc_id, track_info = self.get_cd_info()
            track_count = len(track_info)
            
            if track_count == 0:
                raise CDRipperError("No audio tracks found on CD")
            
            # Lookup metadata
            metadata = self.lookup_musicbrainz(track_count)
            if not metadata:
                self.logger.warning("No metadata found, using defaults")
                metadata = {
                    'album': 'Unknown Album',
                    'artist': 'Unknown Artist', 
                    'date': 'Unknown',
                    'mbid': 'unknown',
                    'tracks': [{'number': i+1, 'title': f'Track {i+1:02d}', 'length': None} 
                              for i in range(track_count)]
                }
            
            # Create album directory
            safe_album_name = f"{metadata['artist']}_{metadata['album']}".replace('/', '_').replace(' ', '_')
            album_dir = self.output_dir / safe_album_name
            album_dir.mkdir(exist_ok=True)
            
            # Download cover art
            cover_path = None
            if metadata['mbid'] != 'unknown':
                cover_path = self.download_cover_art(metadata['mbid'], metadata['album'], metadata['artist'])
            
            # Rip each track
            successful_tracks = 0
            for track in metadata['tracks']:
                track_num = track['number']
                safe_title = track['title'].replace('/', '_').replace(' ', '_')
                flac_filename = f"{track_num:02d}_{safe_title}.flac"
                flac_path = album_dir / flac_filename
                
                if self.rip_track(track_num, flac_path):
                    self.add_metadata(flac_path, metadata, track, cover_path)
                    successful_tracks += 1
                else:
                    self.logger.error(f"Failed to rip track {track_num}")
            
            # Save metadata JSON for reference
            metadata_file = album_dir / "metadata.json"
            with open(metadata_file, 'w') as f:
                json.dump(metadata, f, indent=2)
            
            self.logger.info(f"CD ripping completed. {successful_tracks}/{track_count} tracks successful")
            
            # Eject CD
            try:
                subprocess.run(["eject"], check=False)
            except:
                pass
            
            return successful_tracks == track_count
            
        except Exception as e:
            self.logger.error(f"CD ripping failed: {e}")
            return False

def main():
    """Main entry point"""
    ripper = CDRipper()
    
    print("CD Ripper - Part 1")
    print("Insert CD and press Enter to start ripping...")
    input()
    
    success = ripper.rip_cd()
    
    if success:
        print("CD ripping completed successfully!")
        return 0
    else:
        print("CD ripping failed. Check logs for details.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
