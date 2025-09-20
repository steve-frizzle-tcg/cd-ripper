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
import re
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
        
        # Ensure directories exist
        for dir_path in [self.temp_dir, self.output_dir]:
            dir_path.mkdir(parents=True, exist_ok=True)

    def clean_artist_name(self, artist: str) -> str:
        """Clean and validate artist names, provide fallbacks for problematic data"""
        if not artist or not artist.strip():
            return "Unknown Artist"
        
        # Handle specific problematic cases
        artist = artist.strip()
        if artist in [" & ", "&", " ", "  ", "   "]:
            return "Unknown Artist"
        
        # Clean up common problems
        if artist.startswith(" & "):
            artist = artist[3:].strip()
        if artist.endswith(" & "):
            artist = artist[:-3].strip()
        
        # If still empty or just symbols, fallback
        if not artist or artist.replace("&", "").replace(" ", "").strip() == "":
            return "Unknown Artist"
        
        return artist

    def is_same_artist_different_language(self, name1: str, name2: str) -> bool:
        """Check if two artist names are likely the same person in different languages/scripts"""
        # This is a conservative check - we mostly want to avoid prompting for obvious cases
        # For now, we'll let most different-script names prompt the user to choose
        
        # Check if they're very similar (just different capitalization/spacing)
        name1_clean = ''.join(name1.lower().split())
        name2_clean = ''.join(name2.lower().split())
        
        if name1_clean == name2_clean:
            return True  # Same name, just formatting differences
        
        # For different scripts (like Cyrillic vs Latin), let user choose
        # This is safer than trying to guess if they're the same person
        return False

    def normalize_catalog_number(self, catalog: str) -> str:
        """Normalize catalog number by removing spaces/hyphens and standardizing format"""
        if not catalog:
            return ""
        
        # Remove all spaces and hyphens, convert to uppercase
        normalized = catalog.strip().replace(" ", "").replace("-", "").upper()
        
        return normalized

    def validate_catalog_format(self, catalog: str) -> bool:
        """Basic validation of catalog number format"""
        if not catalog:
            return False
        
        # Most catalog numbers are 6-15 characters, alphanumeric with some special chars
        if len(catalog) < 3 or len(catalog) > 20:
            return False
        
        # Should contain at least some alphanumeric characters
        if not re.search(r'[A-Z0-9]', catalog):
            return False
        
        return True

    def get_catalog_number_with_validation(self) -> Optional[str]:
        """Get and validate catalog number with multiple attempts"""
        print("\n=== Catalog Number (Optional) ===")
        print("Catalog numbers provide the most accurate metadata lookup.")
        print("Common locations: CD spine, back cover, or printed on disc")
        print("Examples: 'GEFD-24617', 'CDV 2644', '7599-26985-2', 'B0001234-02'")
        print("Note: Spaces and hyphens will be automatically normalized")
        
        attempts = 0
        max_attempts = 3
        
        while attempts < max_attempts:
            catalog_input = input(f"Catalog number (Enter to skip, attempt {attempts + 1}/{max_attempts}): ").strip()
            
            if not catalog_input:
                return None
            
            # Normalize the input
            normalized_catalog = self.normalize_catalog_number(catalog_input)
            
            # Validate format
            if not self.validate_catalog_format(normalized_catalog):
                print(f"❌ Invalid catalog number format: '{catalog_input}'")
                print("   Catalog numbers should be 3-20 characters with letters/numbers")
                attempts += 1
                continue
            
            # Show what will be searched and ask for confirmation
            original_input = catalog_input.strip()
            if normalized_catalog != original_input:
                print(f"📝 Will search for: '{original_input}' (original) and '{normalized_catalog}' (normalized) plus common variations")
                confirm = input(f"Use catalog number '{original_input}'? (y/n/retry): ").lower().strip()
            else:
                confirm = input(f"Use catalog number '{original_input}'? (y/n/retry): ").lower().strip()
            
            # Return the original input, not normalized - we'll try both in search
            catalog_to_return = original_input
            
            if confirm in ['y', 'yes', '']:
                return catalog_to_return
            elif confirm in ['n', 'no']:
                return None
            elif confirm in ['r', 'retry']:
                attempts += 1
                continue
            else:
                print("Please enter 'y' for yes, 'n' for no, or 'retry' to try again")
        
        print("❌ Maximum attempts reached. Continuing without catalog number.")
        return None

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

    def get_album_type(self) -> str:
        """Get album type from user"""
        print("\n=== Album Type Selection ===")
        print("1. Regular Album (single artist)")
        print("2. Soundtrack (multiple artists, movie/TV/game soundtrack)")
        print("3. Compilation (multiple artists, various artists collection)")
        
        while True:
            choice = input("Select album type (1-3): ").strip()
            if choice == "1":
                return "regular"
            elif choice == "2":
                return "soundtrack"
            elif choice == "3":
                return "compilation"
            else:
                print("Please enter 1, 2, or 3")

    def get_user_metadata(self) -> Dict:
        """Get basic metadata from user based on album type"""
        album_type = self.get_album_type()
        
        # Get and validate catalog number
        catalog_number = self.get_catalog_number_with_validation()
        
        print(f"\n=== {album_type.title()} Information ===")
        print("Please enter the album information (will be refined later with MusicBrainz lookup):")
        
        if album_type == "regular":
            # Regular album - single artist
            artist = input("Artist name: ").strip() or "Unknown Artist"
            album = input("Album name: ").strip() or "Unknown Album"
            album_artist = artist
        elif album_type == "soundtrack":
            # Soundtrack - various artists
            album = input("Soundtrack name (e.g., 'The Matrix Soundtrack'): ").strip() or "Unknown Soundtrack"
            artist = "Various Artists"
            album_artist = "Various Artists"
            print(f"Artist will be set to: {artist}")
        else:  # compilation
            # Compilation - various artists
            album = input("Compilation name (e.g., 'Now That's What I Call Music 50'): ").strip() or "Unknown Compilation"
            artist = "Various Artists"
            album_artist = "Various Artists"
            print(f"Artist will be set to: {artist}")
        
        year = input("Year (optional): ").strip() or "Unknown"
        
        # Ask for disc number for multi-disc albums
        disc_input = input("Disc number (press Enter for 1): ").strip()
        try:
            disc_number = int(disc_input) if disc_input else 1
            if disc_number < 1:
                disc_number = 1
        except ValueError:
            disc_number = 1
            
        return {
            'artist': artist,
            'album': album,
            'album_artist': album_artist,
            'date': year,
            'disc_number': disc_number,
            'album_type': album_type,
            'catalog_number': catalog_number,
            'mbid': 'user-entered',
            'method': 'manual'
        }

    def _extract_release_metadata(self, release_info: dict, catalog_number: str = None) -> Dict:
        """Extract metadata from MusicBrainz release info"""
        metadata = {
            'mbid': release_info['id'],
            'album': release_info['title'],
            'date': release_info.get('date', ''),
            'country': release_info.get('country', ''),
            'catalog_number': catalog_number,
            'tracks': [],
            'disc_count': len(release_info.get('medium-list', []))
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
                track_info = {
                    'number': track_number,
                    'disc': disc_num,
                    'title': track['recording']['title'],
                    'length': track['recording'].get('length'),
                    'mbid': track['recording']['id']
                }
                
                # Get track artist if different from album artist
                if 'artist-credit' in track['recording']:
                    track_credits = track['recording']['artist-credit']
                    if isinstance(track_credits, list) and track_credits:
                        track_info['artist'] = track_credits[0]['artist']['name']
                
                metadata['tracks'].append(track_info)
                track_number += 1
        
        return metadata

    def search_musicbrainz_by_catalog(self, catalog_number: str, track_count: int) -> Optional[Dict]:
        """Search MusicBrainz by catalog number with enhanced error handling"""
        try:
            # Normalize catalog number for search
            normalized_catalog = self.normalize_catalog_number(catalog_number)
            original_catalog = catalog_number.strip()
            
            self.logger.info(f"Searching MusicBrainz by catalog number: {original_catalog}")
            
            # Build comprehensive search variations
            search_variations = []
            
            # 1. Original user input (most important!)
            search_variations.append(original_catalog)
            
            # 2. Normalized version (no spaces/hyphens)
            if normalized_catalog != original_catalog:
                search_variations.append(normalized_catalog)
            
            # 3. Common space variations based on original input
            if ' ' in original_catalog:
                # Try with hyphens instead of spaces
                with_hyphens = original_catalog.replace(' ', '-')
                search_variations.append(with_hyphens)
                
                # Try without spaces (normalized)
                without_spaces = original_catalog.replace(' ', '')
                if without_spaces not in search_variations:
                    search_variations.append(without_spaces)
            
            # 4. If original had hyphens, try with spaces
            if '-' in original_catalog:
                with_spaces = original_catalog.replace('-', ' ')
                search_variations.append(with_spaces)
            
            # 5. Add common hyphen positions for normalized version (if no spaces/hyphens in original)
            if ' ' not in original_catalog and '-' not in original_catalog and len(normalized_catalog) >= 6:
                # Try common hyphen positions
                variations_with_hyphens = [
                    f"{normalized_catalog[:3]}-{normalized_catalog[3:]}",
                    f"{normalized_catalog[:4]}-{normalized_catalog[4:]}",
                    f"{normalized_catalog[:5]}-{normalized_catalog[5:]}",
                    f"{normalized_catalog[:6]}-{normalized_catalog[6:]}",
                ]
                search_variations.extend(variations_with_hyphens)
            
            # 6. Add common space positions for normalized version (if no spaces/hyphens in original)  
            if ' ' not in original_catalog and '-' not in original_catalog and len(normalized_catalog) >= 6:
                # Try common space positions
                variations_with_spaces = [
                    f"{normalized_catalog[:3]} {normalized_catalog[3:]}",
                    f"{normalized_catalog[:4]} {normalized_catalog[4:]}",
                    f"{normalized_catalog[:5]} {normalized_catalog[5:]}",
                    f"{normalized_catalog[:6]} {normalized_catalog[6:]}",
                ]
                search_variations.extend(variations_with_spaces)
            
            # Remove duplicates while preserving order
            unique_variations = []
            seen = set()
            for variation in search_variations:
                if variation and variation not in seen:
                    unique_variations.append(variation)
                    seen.add(variation)
            
            self.logger.info(f"Will try {len(unique_variations)} catalog variations: {unique_variations}")
            
            found_releases = []
            
            for i, variation in enumerate(unique_variations, 1):
                try:
                    self.logger.info(f"Trying catalog variation {i}/{len(unique_variations)}: '{variation}'")
                    result = musicbrainzngs.search_releases(catno=variation, limit=20)
                    
                    if result['release-list']:
                        found_releases.extend(result['release-list'])
                        self.logger.info(f"✅ Found {len(result['release-list'])} releases for variation: '{variation}'")
                        # Don't break here - we want to collect all matches for deduplication
                    else:
                        self.logger.info(f"❌ No releases found for variation: '{variation}'")
                    
                except Exception as e:
                    self.logger.warning(f"Search failed for catalog variation '{variation}': {e}")
                    continue
            
            if not found_releases:
                self.logger.info(f"No releases found for any catalog variations of: {catalog_number}")
                return None
            
            # Remove duplicates based on MBID
            unique_releases = {}
            for release in found_releases:
                unique_releases[release['id']] = release
            
            self.logger.info(f"Found {len(unique_releases)} unique releases total")
            
            # Look for releases that match our track count
            matching_releases = []
            for release in unique_releases.values():
                try:
                    # Get detailed release info
                    detailed_release = musicbrainzngs.get_release_by_id(
                        release['id'], 
                        includes=['recordings', 'artists', 'labels', 'media']
                    )
                    
                    release_info = detailed_release['release']
                    
                    # Check if track count matches
                    total_tracks = sum(len(medium.get('track-list', [])) 
                                     for medium in release_info.get('medium-list', []))
                    
                    if total_tracks == track_count:
                        matching_releases.append((release_info, total_tracks))
                        self.logger.info(f"✅ Track count match: {release_info['title']} ({total_tracks} tracks)")
                    else:
                        self.logger.debug(f"Track count mismatch: {release_info['title']} ({total_tracks} vs {track_count} tracks)")
                        
                except Exception as e:
                    self.logger.warning(f"Error processing release {release.get('id', 'unknown')}: {e}")
                    continue
            
            if not matching_releases:
                # Show user what was found but didn't match
                print(f"\n📀 Found releases for catalog '{catalog_number}' but none match {track_count} tracks:")
                for release in list(unique_releases.values())[:5]:  # Show first 5
                    print(f"   - {release.get('title', 'Unknown')} by {release.get('artist-credit-phrase', 'Unknown')}")
                print("   Continuing with artist/album search...")
                return None
            
            # If multiple matches, let user choose or take first one
            if len(matching_releases) > 1:
                print(f"\n🔍 Multiple releases found for catalog '{catalog_number}' with {track_count} tracks:")
                for i, (release_info, track_count) in enumerate(matching_releases, 1):
                    artist_name = release_info.get('artist-credit-phrase', 'Unknown Artist')
                    date = release_info.get('date', 'Unknown')
                    country = release_info.get('country', 'Unknown')
                    print(f"   {i}. {release_info['title']} - {artist_name} ({date}, {country})")
                
                while True:
                    choice = input(f"Select release (1-{len(matching_releases)}) or press Enter for first: ").strip()
                    if not choice:
                        selected_release = matching_releases[0][0]
                        break
                    try:
                        choice_num = int(choice)
                        if 1 <= choice_num <= len(matching_releases):
                            selected_release = matching_releases[choice_num - 1][0]
                            break
                        else:
                            print(f"Please enter a number between 1 and {len(matching_releases)}")
                    except ValueError:
                        print("Please enter a valid number")
            else:
                selected_release = matching_releases[0][0]
            
            # Extract and return metadata from selected release
            return self._extract_release_metadata(selected_release, normalized_catalog)
            
        except Exception as e:
            self.logger.error(f"Error searching by catalog number: {e}")
            return None

    def search_musicbrainz_enhanced(self, artist: str, album: str, track_count: int, album_type: str = "regular", catalog_number: str = None) -> Optional[Dict]:
        """Enhanced MusicBrainz search with catalog number priority"""
        
        # First, try catalog number search if provided
        if catalog_number:
            self.logger.info(f"Attempting catalog number search first: {catalog_number}")
            catalog_result = self.search_musicbrainz_by_catalog(catalog_number, track_count)
            if catalog_result:
                self.logger.info("✅ Found exact match by catalog number!")
                return catalog_result
            else:
                self.logger.info("Catalog number search failed, falling back to artist/album search")
        
        # Fall back to existing artist/album search
        try:
            if album_type == "soundtrack":
                self.logger.info(f"Searching MusicBrainz for soundtrack: {album} ({track_count} tracks)")
                # For soundtracks, search by album title and try to find Various Artists releases
                query = f'release:"{album}" AND artist:"Various Artists"'
                self.logger.info("Searching for soundtrack by album title")
            elif album_type == "compilation":
                self.logger.info(f"Searching MusicBrainz for compilation: {album} ({track_count} tracks)")
                # For compilations, search by album title
                query = f'release:"{album}"'
                self.logger.info("Searching for compilation by album title")
            else:
                self.logger.info(f"Searching MusicBrainz for: {artist} - {album} ({track_count} tracks)")
                # Regular album search
                query = f'artist:"{artist}" AND release:"{album}"'
            
            releases = musicbrainzngs.search_releases(query=query, limit=15)
            
            if not releases.get('release-list'):
                self.logger.info("No exact matches found, trying broader search...")
                if album_type == "soundtrack":
                    # Try broader search for soundtracks without artist constraint
                    query = f'release:{album}'
                    self.logger.info("Trying broader soundtrack search")
                elif album_type == "compilation":
                    # Try broader search for compilations
                    query = f'release:{album}'
                    self.logger.info("Trying broader compilation search")
                else:
                    # Try broader search without quotes
                    query = f'artist:{artist} AND release:{album}'
                releases = musicbrainzngs.search_releases(query=query, limit=15)
            
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
            
            # Extract track information and disc information
            tracks = []
            disc_count = len(best_release.get('medium-list', []))
            medium_list = best_release.get('medium-list', [])
            
            for disc_num, medium in enumerate(medium_list, 1):
                disc_tracks = medium.get('track-list', [])
                for track_num, track in enumerate(disc_tracks, 1):
                    recording = track.get('recording', {})
                    
                    # Extract track artist information
                    track_artist = None
                    if 'artist-credit' in track:
                        # Track has specific artist credits
                        artist_credits = track['artist-credit']
                        if artist_credits:
                            # Join multiple artists with " feat. " or " & "
                            artist_names = []
                            for credit in artist_credits:
                                if isinstance(credit, dict) and 'artist' in credit:
                                    artist_names.append(credit['artist'].get('name', ''))
                                elif isinstance(credit, str):
                                    if credit not in [' feat. ', ' & ', ', ']:  # Skip joinphrases
                                        artist_names.append(credit)
                            track_artist = ''.join(str(credit.get('joinphrase', '')) if isinstance(credit, dict) else credit for credit in artist_credits if credit)
                            # Fallback: just join the artist names
                            if not track_artist:
                                track_artist = ' & '.join(filter(None, artist_names))
                    
                    tracks.append({
                        'title': recording.get('title', f"Track {track_num:02d}"),
                        'length': track.get('length'),
                        'disc_number': disc_num,
                        'track_number': track_num,
                        'artist': track_artist  # Individual track artist (None for regular albums)
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
                'disc_count': disc_count,
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

    def download_cover_art_simple(self, mbid: str, artist: str, album: str, album_dir: Path) -> Optional[str]:
        """Simple cover art download with error handling - saves to album directory"""
        try:
            url = f"https://coverartarchive.org/release/{mbid}/front"
            response = requests.get(url, timeout=30, stream=True)
            response.raise_for_status()
            
            # Save cover directly in the album directory
            cover_path = album_dir / "cover.jpg"
            
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
            # Handle directory structure based on album type
            safe_album = new_metadata['album'].replace('/', '_')
            
            if new_metadata.get('album_type') == 'soundtrack':
                # Soundtracks go in output/Soundtracks/Album Name
                new_album_dir = self.output_dir / "Soundtracks" / safe_album
            else:
                # Regular albums and compilations use artist directory
                safe_artist = new_metadata['artist'].replace('/', '_')
                artist_dir = self.output_dir / safe_artist
                new_album_dir = artist_dir / safe_album
            
            if old_album_dir == new_album_dir:
                return old_album_dir  # No change needed
            
            self.logger.info(f"Reorganizing: {old_album_dir} -> {new_album_dir}")
            
            # Create new directory structure
            new_album_dir.mkdir(parents=True, exist_ok=True)
            
            # Move all files from old to new directory
            files_moved = 0
            for file_path in old_album_dir.iterdir():
                if file_path.is_file():
                    new_file_path = new_album_dir / file_path.name
                    file_path.rename(new_file_path)
                    files_moved += 1
                    self.logger.info(f"Moved: {file_path.name}")
            
            self.logger.info(f"Moved {files_moved} files to new location")
            
            # Clean up old directory structure safely
            self.cleanup_empty_directories(old_album_dir.parent, old_album_dir)
            
            return new_album_dir
            
        except Exception as e:
            self.logger.error(f"Failed to reorganize directory: {e}")
            return old_album_dir

    def cleanup_empty_directories(self, artist_dir: Path, album_dir: Path):
        """Safely clean up empty directories after reorganization"""
        try:
            # First, try to remove the album directory
            if album_dir.exists():
                try:
                    # Check if directory is empty
                    if not any(album_dir.iterdir()):
                        album_dir.rmdir()
                        self.logger.info(f"Removed empty album directory: {album_dir}")
                    else:
                        self.logger.warning(f"Album directory not empty, keeping: {album_dir}")
                        remaining_files = list(album_dir.iterdir())
                        self.logger.info(f"Remaining files: {[f.name for f in remaining_files]}")
                        return  # Don't clean up artist dir if album dir has files
                except OSError as e:
                    self.logger.warning(f"Could not remove album directory {album_dir}: {e}")
                    return
            
            # Then, try to remove the artist directory if it's empty
            if artist_dir.exists() and artist_dir != self.output_dir:
                try:
                    # Check if artist directory is empty
                    if not any(artist_dir.iterdir()):
                        artist_dir.rmdir()
                        self.logger.info(f"Removed empty artist directory: {artist_dir}")
                    else:
                        remaining_items = list(artist_dir.iterdir())
                        self.logger.info(f"Artist directory not empty, keeping: {artist_dir}")
                        self.logger.info(f"Contains: {[item.name for item in remaining_items]}")
                except OSError as e:
                    self.logger.warning(f"Could not remove artist directory {artist_dir}: {e}")
                    
        except Exception as e:
            self.logger.error(f"Error during directory cleanup: {e}")

    def rename_track_files(self, album_dir: Path, metadata: Dict, disc_number: int = 1) -> List[Path]:
        """Rename track files with proper names from metadata using Disc-Track format"""
        try:
            flac_files = sorted(album_dir.glob("Track_*.flac"))
            tracks = metadata.get('tracks', [])
            renamed_files = []
            
            for flac_path in flac_files:
                try:
                    # Extract actual track number from filename (Track_02.flac -> 2)
                    match = re.search(r'Track_(\d+)\.flac', flac_path.name)
                    if match:
                        actual_track_num = int(match.group(1))
                        track_index = actual_track_num - 1  # Convert to 0-based index
                    else:
                        # Fallback: use position in sorted list
                        track_index = flac_files.index(flac_path)
                        actual_track_num = track_index + 1
                    
                    if track_index < len(tracks):
                        # Use MusicBrainz track title for the actual track number
                        track_title = tracks[track_index]['title']
                    else:
                        # Fallback to generic name
                        track_title = f"Track {actual_track_num:02d}"
                    
                    # Sanitize filename
                    safe_title = track_title.replace('/', '_').replace('\\', '_').replace(':', '_')
                    safe_title = safe_title.replace('?', '').replace('*', '').replace('"', "'")
                    safe_title = safe_title.replace('<', '').replace('>', '').replace('|', '_')
                    
                    # New format with optional artist for Various Artists releases
                    if track_index < len(tracks) and tracks[track_index].get('artist') and metadata.get('album_type') in ['soundtrack', 'compilation']:
                        # Format: 01-01. Artist - Track Title.flac
                        # Clean the artist name first
                        clean_artist = self.clean_artist_name(tracks[track_index]['artist'])
                        safe_artist = clean_artist.replace('/', '_').replace('\\', '_').replace(':', '_')
                        safe_artist = safe_artist.replace('?', '').replace('*', '').replace('"', "'")
                        safe_artist = safe_artist.replace('<', '').replace('>', '').replace('|', '_')
                        new_filename = f"{disc_number:02d}-{actual_track_num:02d}. {safe_artist} - {safe_title}.flac"
                    else:
                        # Regular format: 01-01. Track Title.flac
                        new_filename = f"{disc_number:02d}-{actual_track_num:02d}. {safe_title}.flac"
                    
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
            
            for flac_path in flac_files:
                try:
                    audio = FLAC(str(flac_path))
                    
                    # Extract track number from filename (01-02. Song.flac -> 2)
                    match = re.search(r'01-(\d+)\.', flac_path.name)
                    if match:
                        actual_track_num = int(match.group(1))
                        track_index = actual_track_num - 1  # Convert to 0-based index
                    else:
                        # Fallback: use position in sorted list
                        track_index = flac_files.index(flac_path)
                        actual_track_num = track_index + 1
                    
                    # Basic metadata
                    audio['ALBUM'] = metadata['album']
                    audio['DATE'] = metadata['date']
                    
                    # Set album artist (for Various Artists releases)
                    if metadata.get('album_artist'):
                        audio['ALBUMARTIST'] = metadata['album_artist']
                    
                    # Enhanced track numbering with proper Vorbis comment format
                    if track_index < len(tracks) and 'disc_number' in tracks[track_index]:
                        disc_num = tracks[track_index]['disc_number']
                        track_num = tracks[track_index]['track_number']
                        audio['TRACKNUMBER'] = f"{track_num:02d}"  # Simple track number (Vorbis standard)
                        audio['DISCNUMBER'] = str(disc_num)
                        audio['TOTALDISCS'] = str(metadata.get('disc_count', 1))
                        audio['TITLE'] = tracks[track_index]['title']
                        
                        # Set track artist (individual track artist or album artist)
                        if tracks[track_index].get('artist'):
                            audio['ARTIST'] = tracks[track_index]['artist']
                        else:
                            audio['ARTIST'] = metadata['artist']
                    else:
                        # Fallback for single disc or unknown structure
                        audio['TRACKNUMBER'] = f"{actual_track_num:02d}"  # Simple track number (Vorbis standard)
                        audio['DISCNUMBER'] = "1"
                        audio['TOTALDISCS'] = "1"
                        audio['ARTIST'] = metadata['artist']
                        if track_index < len(tracks):
                            audio['TITLE'] = tracks[track_index]['title']
                        else:
                            audio['TITLE'] = f"Track {actual_track_num:02d}"
                    
                    audio['TOTALTRACKS'] = str(total_tracks)
                    
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
            disc_number = metadata.get('disc_number', 1)
            
            for flac_path in flac_files:
                try:
                    audio = FLAC(str(flac_path))
                    
                    # Extract track number from filename (01-02. Song.flac -> 2)
                    match = re.search(r'01-(\d+)\.', flac_path.name)
                    if match:
                        actual_track_num = int(match.group(1))
                    else:
                        # Fallback: use position in sorted list + 1
                        actual_track_num = flac_files.index(flac_path) + 1
                    
                    # Basic metadata with proper Vorbis comment format
                    audio['ALBUM'] = metadata['album']
                    audio['DATE'] = metadata['date']
                    audio['TRACKNUMBER'] = f"{actual_track_num:02d}"  # Simple track number (Vorbis standard)
                    audio['DISCNUMBER'] = str(disc_number)
                    audio['TOTALDISCS'] = "1"  # Will be updated if multi-disc detected
                    audio['TOTALTRACKS'] = str(total_tracks)
                    
                    # Set album artist for Various Artists releases
                    if metadata.get('album_artist'):
                        audio['ALBUMARTIST'] = metadata['album_artist']
                    
                    # For Various Artists releases, ask for individual track artists
                    if metadata.get('album_type') in ['soundtrack', 'compilation']:
                        track_artist = input(f"Enter artist for track {actual_track_num} (or press Enter for 'Unknown Artist'): ").strip()
                        audio['ARTIST'] = track_artist or "Unknown Artist"
                    else:
                        audio['ARTIST'] = metadata['artist']
                    
                    # Add track title (user can rename later)
                    track_title = input(f"Enter title for track {actual_track_num} (or press Enter for 'Track {actual_track_num:02d}'): ").strip()
                    audio['TITLE'] = track_title or f"Track {actual_track_num:02d}"
                    
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
            
            # Create album directory using proper structure based on album type
            safe_album = metadata['album'].replace('/', '_')
            
            if metadata.get('album_type') == 'soundtrack':
                # Soundtracks go directly in output/Soundtracks/Album Name
                album_dir = self.output_dir / "Soundtracks" / safe_album
            else:
                # Regular albums and compilations use artist directory structure
                safe_artist = metadata['artist'].replace('/', '_')
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
            
            # Try enhanced MusicBrainz lookup first (with track info and catalog number)
            album_type = metadata.get('album_type', 'regular')
            catalog_number = metadata.get('catalog_number')
            mb_metadata = self.search_musicbrainz_enhanced(
                metadata['artist'], 
                metadata['album'], 
                track_count, 
                album_type,
                catalog_number
            )
            if not mb_metadata:
                # Fallback to simple search
                mb_metadata = self.search_musicbrainz_simple(metadata['artist'], metadata['album'])
            
            if mb_metadata:
                # Handle artist name choice based on album type
                original_artist = metadata['artist']
                mb_artist = mb_metadata.get('artist', original_artist)
                
                if metadata.get('album_type') == 'soundtrack':
                    # For soundtracks, always keep "Various Artists" as artist/album_artist
                    # but use MusicBrainz data for track info and other metadata
                    mb_metadata['artist'] = 'Various Artists'
                    mb_metadata['album_artist'] = 'Various Artists'
                    metadata.update(mb_metadata)
                    self.logger.info("Soundtrack: Using 'Various Artists' for artist/album_artist, MusicBrainz data for tracks")
                elif original_artist.lower() != mb_artist.lower() and not self.is_same_artist_different_language(original_artist, mb_artist):
                    # Ask user for non-soundtrack releases when artist names differ significantly
                    print(f"\n🎵 Artist Name Choice:")
                    print(f"   1. Your input: '{original_artist}' (keeps English/familiar name)")
                    print(f"   2. MusicBrainz: '{mb_artist}' (official database name)")
                    print(f"   Note: This affects folder organization (output/{original_artist}/ vs output/{mb_artist}/)")
                    choice = input("Use (1) Your input or (2) MusicBrainz version? [1]: ").strip()
                    if choice == "2":
                        # Use MusicBrainz artist
                        metadata.update(mb_metadata)
                        self.logger.info(f"Using MusicBrainz artist name: '{mb_artist}'")
                    else:
                        # Keep original artist, but use other MusicBrainz data
                        mb_metadata['artist'] = original_artist
                        mb_metadata['album_artist'] = original_artist
                        metadata.update(mb_metadata)
                        self.logger.info(f"Keeping original artist name: '{original_artist}'")
                else:
                    # Use MusicBrainz data as-is (names are similar)
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
                    metadata['album'],
                    album_dir
                )
            
            # Get FLAC files and add metadata
            flac_files = sorted(album_dir.glob("Track_*.flac"))
            if flac_files:
                # Use disc number from user input or MusicBrainz data
                disc_number = metadata.get('disc_number', 1)
                
                if metadata.get('tracks'):
                    # Enhanced metadata with track names
                    flac_files = self.rename_track_files(album_dir, metadata, disc_number=disc_number)
                    self.add_enhanced_metadata(flac_files, metadata, cover_path)
                else:
                    # Basic metadata - ask user for track names
                    flac_files = self.rename_track_files(album_dir, metadata, disc_number=disc_number)
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
    
    print("=== CD Ripper - Enhanced Version ===")
    print("This script will:")
    print("1. Rip all tracks to FLAC files")
    print("2. Add metadata (supports Regular Albums, Soundtracks, and Compilations)")
    print("3. Handle Various Artists releases with per-track artist information")
    print("4. Optionally download cover art")
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