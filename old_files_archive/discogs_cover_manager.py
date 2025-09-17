#!/usr/bin/env python3
"""
Discogs Cover Art Manager
Finds and downloads album covers using the Discogs API with proper authentication.
"""

import os
import sys
import json
import requests
import time
from pathlib import Path
from typing import Optional, Dict, List, Tuple
from PIL import Image
from mutagen.flac import FLAC, Picture
import base64

class DiscogsAPI:
    """Handles Discogs API authentication and requests"""
    
    def __init__(self):
        self.base_url = "https://api.discogs.com"
        self.session = requests.Session()
        self.rate_limit_remaining = 60
        self.rate_limit_reset = 0
        self.config_file = Path.home() / '.discogs_config.json'
        
    def setup_authentication(self) -> bool:
        """Setup Discogs API authentication"""
        print("🎵 Discogs API Authentication Setup")
        print("=" * 50)
        print("\nTo use the Discogs API, you need to create a personal access token:")
        print("1. Go to https://www.discogs.com/settings/developers")
        print("2. Click 'Generate new token'")
        print("3. Give it a name like 'CD Ripper Cover Art'")
        print("4. Copy the token\n")
        
        # Check if we already have stored credentials
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r') as f:
                    config = json.load(f)
                token = config.get('token')
                if token:
                    print("Found existing token. Testing authentication...")
                    if self.test_authentication(token):
                        self.session.headers.update({
                            'Authorization': f'Discogs token={token}',
                            'User-Agent': 'CDRipperCoverArt/1.0'
                        })
                        return True
                    else:
                        print("❌ Stored token is invalid")
            except Exception as e:
                print(f"Error reading config: {e}")
        
        # Get new token from user
        while True:
            token = input("Enter your Discogs personal access token: ").strip()
            if not token:
                print("❌ Token cannot be empty")
                continue
                
            if self.test_authentication(token):
                # Save token
                try:
                    with open(self.config_file, 'w') as f:
                        json.dump({'token': token}, f)
                    os.chmod(self.config_file, 0o600)  # Secure permissions
                    print("✅ Token saved successfully")
                except Exception as e:
                    print(f"Warning: Could not save token: {e}")
                
                self.session.headers.update({
                    'Authorization': f'Discogs token={token}',
                    'User-Agent': 'CDRipperCoverArt/1.0'
                })
                return True
            else:
                print("❌ Invalid token. Please try again.")
                retry = input("Try again? (y/n): ").lower()
                if retry != 'y':
                    return False
    
    def test_authentication(self, token: str) -> bool:
        """Test if the token is valid"""
        try:
            headers = {
                'Authorization': f'Discogs token={token}',
                'User-Agent': 'CDRipperCoverArt/1.0'
            }
            response = requests.get(f"{self.base_url}/oauth/identity", headers=headers, timeout=10)
            if response.status_code == 200:
                user_info = response.json()
                print(f"✅ Authenticated as: {user_info.get('username', 'Unknown')}")
                return True
            return False
        except Exception as e:
            print(f"Authentication test failed: {e}")
            return False
    
    def handle_rate_limit(self, response: requests.Response):
        """Handle Discogs API rate limiting"""
        self.rate_limit_remaining = int(response.headers.get('x-discogs-ratelimit-remaining', 60))
        self.rate_limit_reset = int(response.headers.get('x-discogs-ratelimit-reset', 0))
        
        if self.rate_limit_remaining <= 5:
            wait_time = max(60, self.rate_limit_reset - int(time.time()))
            print(f"⏳ Rate limit low ({self.rate_limit_remaining} remaining). Waiting {wait_time}s...")
            time.sleep(wait_time)
    
    def search_releases(self, artist: str, album: str) -> List[Dict]:
        """Search for releases on Discogs"""
        try:
            # Clean up search terms
            artist_clean = artist.replace('/', ' ').replace('&', 'and').strip()
            album_clean = album.replace('/', ' ').replace('&', 'and').strip()
            
            # Try different search strategies
            search_queries = [
                f'artist:"{artist_clean}" release_title:"{album_clean}"',
                f'"{artist_clean}" "{album_clean}"',
                f'{artist_clean} {album_clean}'
            ]
            
            for query in search_queries:
                params = {
                    'q': query,
                    'type': 'release',
                    'per_page': 25,
                    'page': 1
                }
                
                response = self.session.get(f"{self.base_url}/database/search", params=params, timeout=15)
                self.handle_rate_limit(response)
                
                if response.status_code == 200:
                    data = response.json()
                    if data.get('results'):
                        return data['results']
                elif response.status_code == 429:
                    print("⏳ Rate limited, waiting...")
                    time.sleep(60)
                    continue
                else:
                    print(f"Search failed: {response.status_code}")
            
            return []
        except Exception as e:
            print(f"Search error: {e}")
            return []
    
    def get_release_details(self, release_id: str) -> Optional[Dict]:
        """Get detailed release information including images"""
        try:
            response = self.session.get(f"{self.base_url}/releases/{release_id}", timeout=15)
            self.handle_rate_limit(response)
            
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 429:
                print("⏳ Rate limited, waiting...")
                time.sleep(60)
                return self.get_release_details(release_id)
            else:
                print(f"Failed to get release details: {response.status_code}")
                return None
        except Exception as e:
            print(f"Error getting release details: {e}")
            return None


class DiscogsCoverManager:
    """Main cover art management class"""
    
    def __init__(self):
        self.api = DiscogsAPI()
        self.temp_dir = Path('/tmp/discogs_covers')
        self.temp_dir.mkdir(exist_ok=True)
    
    def find_missing_covers(self, output_dir: Path) -> List[Path]:
        """Find albums missing cover art files"""
        missing_covers = []
        
        for artist_dir in output_dir.iterdir():
            if not artist_dir.is_dir():
                continue
                
            for album_dir in artist_dir.iterdir():
                if not album_dir.is_dir():
                    continue
                
                # Check for cover files
                cover_files = list(album_dir.glob('cover.*')) + list(album_dir.glob('folder.*'))
                
                if not cover_files:
                    missing_covers.append(album_dir)
        
        return missing_covers
    
    def display_search_results(self, results: List[Dict], artist: str, album: str) -> Optional[str]:
        """Display search results and let user choose"""
        if not results:
            print(f"❌ No results found for {artist} / {album}")
            return None
        
        print(f"\n🔍 Search results for: {artist} / {album}")
        print("=" * 60)
        
        # Filter and score results
        scored_results = []
        for i, result in enumerate(results[:10]):  # Limit to top 10
            title = result.get('title', 'Unknown')
            year = result.get('year', 'Unknown')
            format_info = ', '.join(result.get('format', [])) or 'Unknown'
            country = result.get('country', 'Unknown')
            
            # Simple scoring based on title matching
            score = 0
            if artist.lower() in title.lower():
                score += 2
            if album.lower() in title.lower():
                score += 2
            if any(fmt in format_info.lower() for fmt in ['cd', 'album']):
                score += 1
                
            scored_results.append((score, i, result, title, year, format_info, country))
        
        # Sort by score (highest first)
        scored_results.sort(key=lambda x: x[0], reverse=True)
        
        # Display options
        for idx, (score, orig_idx, result, title, year, format_info, country) in enumerate(scored_results):
            print(f"{idx + 1:2d}. {title}")
            print(f"     📅 {year} | 💿 {format_info} | 🌍 {country}")
            if score >= 3:
                print("     ⭐ High match confidence")
            print()
        
        print("  0. Skip this album")
        print(" 98. Manual search (enter custom query)")
        print(" 99. Exit")
        
        while True:
            try:
                choice = input(f"\nSelect option (1-{len(scored_results)}, 0, 98, 99): ").strip()
                
                if choice == '0':
                    return None
                elif choice == '98':
                    custom_query = input("Enter custom search query: ").strip()
                    if custom_query:
                        custom_results = self.api.search_releases('', custom_query)
                        return self.display_search_results(custom_results, artist, album)
                    continue
                elif choice == '99':
                    sys.exit(0)
                else:
                    choice_idx = int(choice) - 1
                    if 0 <= choice_idx < len(scored_results):
                        selected = scored_results[choice_idx][2]
                        return str(selected['id'])
                    else:
                        print(f"Invalid choice. Please enter 1-{len(scored_results)}, 0, 98, or 99")
            except (ValueError, KeyError):
                print("Invalid input. Please try again.")
    
    def download_cover_image(self, image_url: str, album_dir: Path, release_details: Dict) -> Optional[Path]:
        """Download and save cover image with fallback options"""
        try:
            print(f"📥 Downloading cover image...")
            
            # Try with session headers (includes authentication)
            response = self.api.session.get(image_url, timeout=30, stream=True)
            
            # If 403, try different approaches
            if response.status_code == 403:
                print("⚠️  Direct image download blocked by Discogs")
                return self.handle_blocked_image(release_details, album_dir)
            
            response.raise_for_status()
            
            # Determine file extension from content type or URL
            content_type = response.headers.get('content-type', '').lower()
            if 'jpeg' in content_type or 'jpg' in content_type:
                ext = '.jpg'
            elif 'png' in content_type:
                ext = '.png'
            else:
                # Fallback to URL extension
                ext = '.jpg'  # Default
                if image_url.lower().endswith('.png'):
                    ext = '.png'
            
            # Save to temporary file first
            temp_path = self.temp_dir / f"cover_{int(time.time())}{ext}"
            
            with open(temp_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            # Validate image
            try:
                with Image.open(temp_path) as img:
                    width, height = img.size
                    print(f"✅ Downloaded image: {width}x{height}")
                    
                    # Resize if too large (max 1000x1000)
                    if width > 1000 or height > 1000:
                        print("🔄 Resizing large image...")
                        img.thumbnail((1000, 1000), Image.Resampling.LANCZOS)
                        img.save(temp_path, optimize=True, quality=95)
            except Exception as e:
                print(f"❌ Invalid image file: {e}")
                temp_path.unlink(missing_ok=True)
                return None
            
            # Move to album directory
            final_path = album_dir / f"cover{ext}"
            import shutil
            shutil.move(str(temp_path), str(final_path))
            
            print(f"✅ Cover saved: {final_path}")
            return final_path
            
        except Exception as e:
            print(f"❌ Failed to download image: {e}")
            return self.handle_blocked_image(release_details, album_dir)
    
    def handle_blocked_image(self, release_details: Dict, album_dir: Path) -> Optional[Path]:
        """Handle cases where Discogs blocks direct image downloads"""
        print("\n🔄 Alternative options for getting cover art:")
        print("1. Manual download from Discogs website")
        print("2. Search alternative sources (MusicBrainz, etc.)")
        print("3. Skip this album")
        
        while True:
            choice = input("Choose option (1-3): ").strip()
            
            if choice == '1':
                return self.manual_discogs_download(release_details, album_dir)
            elif choice == '2':
                return self.search_alternative_sources(album_dir)
            elif choice == '3':
                return None
            else:
                print("Invalid choice. Please enter 1, 2, or 3.")
    
    def manual_discogs_download(self, release_details: Dict, album_dir: Path) -> Optional[Path]:
        """Guide user through manual download from Discogs"""
        release_url = f"https://www.discogs.com/release/{release_details['id']}"
        
        print(f"\n📋 Manual Download Instructions:")
        print(f"1. Open this URL in your browser: {release_url}")
        print(f"2. Right-click on the album cover image")
        print(f"3. Save the image to: {album_dir}")
        print(f"4. Name the file 'cover.jpg' or 'cover.png'")
        print(f"5. Press Enter when done, or 's' to skip")
        
        input("Press Enter when you've saved the cover image...")
        
        # Check if user added the cover
        cover_files = list(album_dir.glob('cover.*'))
        if cover_files:
            cover_path = cover_files[0]
            print(f"✅ Found cover: {cover_path}")
            
            # Add to FLAC files
            self.add_cover_to_flac_files(album_dir, cover_path)
            return cover_path
        else:
            print("❌ No cover file found")
            return None
    
    def search_alternative_sources(self, album_dir: Path) -> Optional[Path]:
        """Search for cover art from alternative sources"""
        artist = album_dir.parent.name
        album = album_dir.name
        
        print(f"\n🔍 Alternative sources for {artist} / {album}:")
        print("1. MusicBrainz Cover Art Archive")
        print("2. Manual search on Google Images")
        print("3. Skip")
        
        while True:
            choice = input("Choose option (1-3): ").strip()
            
            if choice == '1':
                return self.search_musicbrainz_covers(artist, album, album_dir)
            elif choice == '2':
                return self.manual_google_search(artist, album, album_dir)
            elif choice == '3':
                return None
            else:
                print("Invalid choice. Please enter 1, 2, or 3.")
    
    def search_musicbrainz_covers(self, artist: str, album: str, album_dir: Path) -> Optional[Path]:
        """Search MusicBrainz Cover Art Archive"""
        try:
            import musicbrainzngs
            
            musicbrainzngs.set_useragent("CDRipperCoverArt", "1.0")
            
            # Search for release
            result = musicbrainzngs.search_releases(
                artist=artist,
                release=album,
                limit=5
            )
            
            releases = result.get('release-list', [])
            if not releases:
                print("❌ No releases found on MusicBrainz")
                return None
            
            print(f"🎵 Found {len(releases)} MusicBrainz releases:")
            for i, release in enumerate(releases):
                title = release.get('title', 'Unknown')
                artist_name = release.get('artist-credit', [{}])[0].get('artist', {}).get('name', 'Unknown')
                print(f"{i+1}. {artist_name} - {title}")
            
            while True:
                try:
                    choice = input(f"Select release (1-{len(releases)}, 0 to skip): ").strip()
                    if choice == '0':
                        return None
                    
                    idx = int(choice) - 1
                    if 0 <= idx < len(releases):
                        release_id = releases[idx]['id']
                        return self.download_musicbrainz_cover(release_id, album_dir)
                    else:
                        print(f"Invalid choice. Please enter 1-{len(releases)} or 0")
                except ValueError:
                    print("Invalid input. Please enter a number.")
                    
        except ImportError:
            print("❌ MusicBrainz library not available")
            return None
        except Exception as e:
            print(f"❌ MusicBrainz search failed: {e}")
            return None
    
    def download_musicbrainz_cover(self, release_id: str, album_dir: Path) -> Optional[Path]:
        """Download cover from MusicBrainz Cover Art Archive"""
        try:
            import musicbrainzngs
            
            # Try to get cover art
            data = musicbrainzngs.get_image_list(release_id)
            images = data.get('images', [])
            
            if not images:
                print("❌ No cover art found in MusicBrainz")
                return None
            
            # Get the front cover
            front_images = [img for img in images if img.get('front', False)]
            if not front_images:
                front_images = images  # Fallback to any image
            
            image = front_images[0]
            image_url = image.get('image')
            
            if not image_url:
                print("❌ No image URL found")
                return None
            
            print("📥 Downloading from MusicBrainz...")
            response = requests.get(image_url, timeout=30, stream=True)
            response.raise_for_status()
            
            # Save image
            ext = '.jpg'  # MusicBrainz usually serves JPEG
            temp_path = self.temp_dir / f"cover_{int(time.time())}{ext}"
            
            with open(temp_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            # Move to album directory
            final_path = album_dir / f"cover{ext}"
            import shutil
            shutil.move(str(temp_path), str(final_path))
            
            print(f"✅ Downloaded from MusicBrainz: {final_path}")
            return final_path
            
        except Exception as e:
            print(f"❌ MusicBrainz download failed: {e}")
            return None
    
    def manual_google_search(self, artist: str, album: str, album_dir: Path) -> Optional[Path]:
        """Guide user through manual Google Images search"""
        search_query = f"{artist} {album} album cover"
        google_url = f"https://www.google.com/search?q={requests.utils.quote(search_query)}&tbm=isch"
        
        print(f"\n📋 Manual Google Images Search:")
        print(f"1. Open this URL: {google_url}")
        print(f"2. Find a high-quality album cover image")
        print(f"3. Right-click and save to: {album_dir}")
        print(f"4. Name the file 'cover.jpg' or 'cover.png'")
        print(f"5. Press Enter when done")
        
        input("Press Enter when you've saved the cover image...")
        
        # Check if user added the cover
        cover_files = list(album_dir.glob('cover.*'))
        if cover_files:
            cover_path = cover_files[0]
            print(f"✅ Found cover: {cover_path}")
            return cover_path
        else:
            print("❌ No cover file found")
            return None
    
    def add_cover_to_flac_files(self, album_dir: Path, cover_path: Path):
        """Add cover art to all FLAC files in the album directory"""
        try:
            print("🎵 Adding cover art to FLAC files...")
            
            # Read cover image
            with open(cover_path, 'rb') as f:
                cover_data = f.read()
            
            # Determine MIME type
            if cover_path.suffix.lower() == '.png':
                mime_type = 'image/png'
            else:
                mime_type = 'image/jpeg'
            
            # Find all FLAC files
            flac_files = list(album_dir.glob('*.flac'))
            
            if not flac_files:
                print("❌ No FLAC files found in album directory")
                return
            
            updated_count = 0
            for flac_path in flac_files:
                try:
                    audio = FLAC(flac_path)
                    
                    # Clear existing pictures
                    audio.clear_pictures()
                    
                    # Create new picture
                    picture = Picture()
                    picture.type = 3  # Cover (front)
                    picture.mime = mime_type
                    picture.desc = 'Cover'
                    picture.data = cover_data
                    
                    # Add picture to FLAC
                    audio.add_picture(picture)
                    audio.save()
                    
                    updated_count += 1
                    
                except Exception as e:
                    print(f"❌ Failed to update {flac_path.name}: {e}")
            
            print(f"✅ Updated {updated_count}/{len(flac_files)} FLAC files with cover art")
            
        except Exception as e:
            print(f"❌ Failed to add cover art to FLAC files: {e}")
    
    def process_album(self, album_dir: Path) -> bool:
        """Process a single album to find and add cover art"""
        artist = album_dir.parent.name
        album = album_dir.name
        
        print(f"\n🎵 Processing: {artist} / {album}")
        print("=" * 80)
        
        # Search for releases
        results = self.api.search_releases(artist, album)
        
        # Let user choose release
        release_id = self.display_search_results(results, artist, album)
        
        if not release_id:
            print("⏭️  Skipping album")
            return False
        
        # Get release details
        print("📋 Getting release details...")
        release_details = self.api.get_release_details(release_id)
        
        if not release_details:
            print("❌ Failed to get release details")
            return False
        
        # Show release info
        title = release_details.get('title', 'Unknown')
        year = release_details.get('year', 'Unknown')
        formats = ', '.join([f.get('name', '') for f in release_details.get('formats', [])])
        
        print(f"📀 Selected: {title} ({year})")
        print(f"💿 Format: {formats}")
        
        # Get images
        images = release_details.get('images', [])
        if not images:
            print("❌ No images found for this release")
            return False
        
        # Filter for primary/cover images
        cover_images = [img for img in images if img.get('type') == 'primary']
        if not cover_images:
            cover_images = images  # Fallback to any image
        
        print(f"🖼️  Found {len(cover_images)} cover image(s)")
        
        # Use the first/best image
        selected_image = cover_images[0]
        image_url = selected_image.get('uri')
        
        if not image_url:
            print("❌ No image URL found")
            return False
        
        # Download image
        cover_path = self.download_cover_image(image_url, album_dir, release_details)
        
        if not cover_path:
            return False
        
        # Add to FLAC files
        self.add_cover_to_flac_files(album_dir, cover_path)
        
        # Update rip_info.json if it exists
        rip_info_path = album_dir / 'rip_info.json'
        if rip_info_path.exists():
            try:
                with open(rip_info_path, 'r') as f:
                    rip_info = json.load(f)
                
                rip_info['cover_art'] = cover_path.name
                rip_info['discogs_release_id'] = release_id
                
                with open(rip_info_path, 'w') as f:
                    json.dump(rip_info, f, indent=2)
                    
                print("✅ Updated rip_info.json")
            except Exception as e:
                print(f"⚠️  Could not update rip_info.json: {e}")
        
        print("✅ Album processing complete!")
        return True


def main():
    """Main function"""
    if len(sys.argv) != 2:
        print("Usage: python3 discogs_cover_manager.py <output_directory>")
        print("Example: python3 discogs_cover_manager.py output")
        sys.exit(1)
    
    output_dir = Path(sys.argv[1])
    if not output_dir.exists():
        print(f"❌ Output directory does not exist: {output_dir}")
        sys.exit(1)
    
    manager = DiscogsCoverManager()
    
    # Setup authentication
    if not manager.api.setup_authentication():
        print("❌ Authentication failed. Exiting.")
        sys.exit(1)
    
    # Find missing covers
    print("\n🔍 Scanning for albums missing cover art...")
    missing_covers = manager.find_missing_covers(output_dir)
    
    if not missing_covers:
        print("✅ All albums have cover art!")
        return
    
    print(f"\n📋 Found {len(missing_covers)} albums missing cover art:")
    for album_dir in missing_covers:
        artist = album_dir.parent.name
        album = album_dir.name
        print(f"   • {artist} / {album}")
    
    print(f"\n🎵 Starting interactive cover art search...")
    print("=" * 80)
    
    processed = 0
    successful = 0
    
    for album_dir in missing_covers:
        try:
            if manager.process_album(album_dir):
                successful += 1
            processed += 1
            
            # Small delay to be nice to the API
            time.sleep(1)
            
        except KeyboardInterrupt:
            print("\n⏹️  Process interrupted by user")
            break
        except Exception as e:
            print(f"❌ Unexpected error processing {album_dir}: {e}")
    
    print("\n📊 Summary:")
    print(f"   Processed: {processed}/{len(missing_covers)}")
    print(f"   Successful: {successful}")
    print(f"   Remaining: {len(missing_covers) - processed}")


if __name__ == "__main__":
    main()
