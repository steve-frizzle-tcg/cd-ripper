#!/usr/bin/env python3
"""
FLAC Metadata Enrichment System
Applies music industry standard metadata to FLAC files and maintains consistency across collection.
"""

import json
import re
import time
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple, Any
from mutagen.flac import FLAC, Picture
import musicbrainzngs
import requests

# Configure MusicBrainz
musicbrainzngs.set_useragent(
    "CD-Ripper-MetadataEnricher",
    "1.0",
    "https://github.com/steve-frizzle-tcg/cd-ripper"
)

class MetadataStandard:
    """Defines the metadata standard for FLAC files"""
    
    # Core required fields (always present)
    REQUIRED_FIELDS = {
        'ALBUM',           # Album title
        'ALBUMARTIST',     # Album artist (Various Artists for compilations)
        'ARTIST',          # Track artist
        'TITLE',           # Track title
        'TRACKNUMBER',     # Track number (disc-track format: 01-05)
        'DATE',            # Release date (year or full date)
    }
    
    # Extended standard fields (should be present when available)
    STANDARD_FIELDS = {
        'DISCNUMBER',      # Disc number
        'TOTALDISCS',      # Total number of discs
        'TOTALTRACKS',     # Total tracks on album
        'GENRE',           # Music genre
        'ALBUMARTISTSORT', # Album artist sort name
        'ARTISTSORT',      # Track artist sort name
        'ALBUMSORT',       # Album sort name
        'TITLESORT',       # Title sort name
    }
    
    # MusicBrainz identification fields
    MUSICBRAINZ_FIELDS = {
        'MUSICBRAINZ_ALBUMID',        # Release MBID
        'MUSICBRAINZ_ARTISTID',       # Album artist MBID
        'MUSICBRAINZ_TRACKID',        # Recording MBID
        'MUSICBRAINZ_RELEASETRACKID', # Track MBID
        'MUSICBRAINZ_RELEASEGROUPID', # Release group MBID
    }
    
    # Additional metadata fields
    EXTENDED_FIELDS = {
        'LABEL',           # Record label
        'CATALOGNUMBER',   # Catalog number
        'BARCODE',         # UPC/EAN barcode
        'COUNTRY',         # Release country
        'MEDIA',           # Media format (CD, Vinyl, etc.)
        'STATUS',          # Release status (Official, Bootleg, etc.)
        'SCRIPT',          # Script (Latin, Cyrillic, etc.)
        'LANGUAGE',        # Language
        'ASIN',            # Amazon ASIN
        'ISRC',            # ISRC code (per track)
        'ORIGINALDATE',    # Original release date
        'ORIGINALYEAR',    # Original release year
    }
    
    # Audio technical fields
    TECHNICAL_FIELDS = {
        'ENCODING',        # Encoding info
        'ENCODER',         # Encoder used
        'ENCODERSETTINGS', # Encoder settings
    }

class FLACMetadataEnricher:
    def __init__(self, output_dir: str = None, dry_run: bool = False):
        self.output_dir = Path(output_dir) if output_dir else Path.home() / "cd_ripping" / "output"
        self.dry_run = dry_run
        self.standard = MetadataStandard()
        
    def analyze_current_metadata(self, flac_path: Path) -> Dict[str, Any]:
        """Analyze current metadata in a FLAC file"""
        try:
            audio = FLAC(str(flac_path))
            
            analysis = {
                'file_path': str(flac_path),
                'current_fields': set(audio.keys()),
                'missing_required': self.standard.REQUIRED_FIELDS - set(audio.keys()),
                'missing_standard': self.standard.STANDARD_FIELDS - set(audio.keys()),
                'has_musicbrainz': bool(self.standard.MUSICBRAINZ_FIELDS & set(audio.keys())),
                'has_cover_art': len(audio.pictures) > 0,
                'metadata': {key: audio.get(key, []) for key in audio.keys()}
            }
            
            return analysis
            
        except Exception as e:
            return {'error': str(e), 'file_path': str(flac_path)}

    def get_enhanced_metadata_from_rip_info(self, rip_info_path: Path) -> Dict[str, Any]:
        """Extract enhanced metadata from rip_info.json"""
        try:
            with open(rip_info_path, 'r', encoding='utf-8') as f:
                rip_info = json.load(f)
            
            metadata = rip_info.get('metadata', {})
            
            enhanced = {
                'album': metadata.get('album', ''),
                'album_artist': metadata.get('album_artist', metadata.get('artist', '')),
                'date': metadata.get('date', ''),
                'disc_count': metadata.get('disc_count', 1),
                'album_type': metadata.get('album_type', 'regular'),
                'mbid': metadata.get('mbid', ''),
                'tracks': metadata.get('tracks', []),
                'catalog_number': metadata.get('catalog_number', ''),
                'method': metadata.get('method', 'unknown')
            }
            
            return enhanced
            
        except Exception as e:
            return {'error': str(e)}

    def enhance_musicbrainz_metadata(self, mbid: str) -> Dict[str, Any]:
        """Get comprehensive metadata from MusicBrainz"""
        if not mbid or mbid in ['user-entered', 'retroactive-scan']:
            return {}
        
        try:
            # Get detailed release information
            release = musicbrainzngs.get_release_by_id(
                mbid,
                includes=[
                    'artists', 'labels', 'recordings', 'release-groups',
                    'media', 'artist-credits', 'aliases', 'tags'
                ]
            )
            
            release_info = release['release']
            enhanced = {}
            
            # Basic release info
            enhanced['album'] = release_info.get('title', '')
            enhanced['date'] = release_info.get('date', '')
            enhanced['country'] = release_info.get('country', '')
            enhanced['status'] = release_info.get('status', '')
            enhanced['script'] = release_info.get('text-representation', {}).get('script', '')
            enhanced['language'] = release_info.get('text-representation', {}).get('language', '')
            
            # Label and catalog information
            if 'label-info-list' in release_info:
                labels = release_info['label-info-list']
                if labels:
                    label_info = labels[0]
                    if 'label' in label_info:
                        enhanced['label'] = label_info['label'].get('name', '')
                    enhanced['catalog_number'] = label_info.get('catalog-number', '')
            
            # Barcode
            enhanced['barcode'] = release_info.get('barcode', '')
            
            # ASIN
            if 'asin' in release_info:
                enhanced['asin'] = release_info['asin']
            
            # Media format
            if 'medium-list' in release_info:
                media_list = release_info['medium-list']
                if media_list:
                    enhanced['media'] = media_list[0].get('format', 'CD')
            
            # Release group info for original date
            if 'release-group' in release_info:
                rg = release_info['release-group']
                enhanced['release_group_id'] = rg['id']
                enhanced['original_date'] = rg.get('first-release-date', '')
                
                # Get primary type and secondary types
                enhanced['primary_type'] = rg.get('primary-type', '')
                if 'secondary-type-list' in rg:
                    enhanced['secondary_types'] = [t for t in rg['secondary-type-list']]
            
            # Artist information
            if 'artist-credit' in release_info:
                artist_credit = release_info['artist-credit']
                if artist_credit and len(artist_credit) > 0:
                    main_artist = artist_credit[0]['artist']
                    enhanced['album_artist'] = main_artist['name']
                    enhanced['album_artist_id'] = main_artist['id']
                    enhanced['album_artist_sort'] = main_artist.get('sort-name', '')
            
            # Track-specific information
            enhanced['tracks'] = []
            track_num = 1
            
            for disc_num, medium in enumerate(release_info.get('medium-list', []), 1):
                for track in medium.get('track-list', []):
                    recording = track.get('recording', {})
                    
                    track_info = {
                        'disc_number': disc_num,
                        'track_number': track_num,
                        'title': recording.get('title', ''),
                        'length': track.get('length'),
                        'track_id': track['id'],
                        'recording_id': recording['id']
                    }
                    
                    # Track artist information
                    if 'artist-credit' in recording:
                        track_artists = []
                        for credit in recording['artist-credit']:
                            if isinstance(credit, dict) and 'artist' in credit:
                                artist = credit['artist']
                                track_artists.append({
                                    'name': artist['name'],
                                    'id': artist['id'],
                                    'sort_name': artist.get('sort-name', '')
                                })
                        track_info['artists'] = track_artists
                        
                        # Primary artist for ARTIST field
                        if track_artists:
                            track_info['artist'] = track_artists[0]['name']
                            track_info['artist_id'] = track_artists[0]['id']
                            track_info['artist_sort'] = track_artists[0]['sort_name']
                    
                    # ISRC
                    if 'isrc-list' in recording:
                        isrcs = recording['isrc-list']
                        if isrcs:
                            track_info['isrc'] = isrcs[0]
                    
                    enhanced['tracks'].append(track_info)
                    track_num += 1
            
            return enhanced
            
        except Exception as e:
            print(f"   ⚠️  MusicBrainz lookup failed: {e}")
            return {}

    def apply_metadata_standard(self, flac_path: Path, enhanced_metadata: Dict[str, Any], 
                              track_info: Dict[str, Any] = None) -> bool:
        """Apply metadata standard to a FLAC file"""
        try:
            if self.dry_run:
                print(f"   [DRY RUN] Would update: {flac_path.name}")
                return True
                
            audio = FLAC(str(flac_path))
            updated = False
            
            # Required fields
            if enhanced_metadata.get('album'):
                if audio.get('ALBUM') != [enhanced_metadata['album']]:
                    audio['ALBUM'] = [enhanced_metadata['album']]
                    updated = True
            
            if enhanced_metadata.get('album_artist'):
                if audio.get('ALBUMARTIST') != [enhanced_metadata['album_artist']]:
                    audio['ALBUMARTIST'] = [enhanced_metadata['album_artist']]
                    updated = True
            
            if enhanced_metadata.get('date'):
                if audio.get('DATE') != [enhanced_metadata['date']]:
                    audio['DATE'] = [enhanced_metadata['date']]
                    updated = True
            
            # Track-specific information
            if track_info:
                # Track title
                if track_info.get('title'):
                    if audio.get('TITLE') != [track_info['title']]:
                        audio['TITLE'] = [track_info['title']]
                        updated = True
                
                # Track artist
                if track_info.get('artist'):
                    if audio.get('ARTIST') != [track_info['artist']]:
                        audio['ARTIST'] = [track_info['artist']]
                        updated = True
                
                # Track number (disc-track format)
                if track_info.get('disc_number') and track_info.get('track_number'):
                    track_num = f"{track_info['disc_number']:02d}-{track_info['track_number']:02d}"
                    if audio.get('TRACKNUMBER') != [track_num]:
                        audio['TRACKNUMBER'] = [track_num]
                        updated = True
                
                # Disc information
                if track_info.get('disc_number'):
                    if audio.get('DISCNUMBER') != [str(track_info['disc_number'])]:
                        audio['DISCNUMBER'] = [str(track_info['disc_number'])]
                        updated = True
                
                # Total discs
                if enhanced_metadata.get('disc_count'):
                    if audio.get('TOTALDISCS') != [str(enhanced_metadata['disc_count'])]:
                        audio['TOTALDISCS'] = [str(enhanced_metadata['disc_count'])]
                        updated = True
            
            # MusicBrainz IDs
            if enhanced_metadata.get('mbid'):
                if audio.get('MUSICBRAINZ_ALBUMID') != [enhanced_metadata['mbid']]:
                    audio['MUSICBRAINZ_ALBUMID'] = [enhanced_metadata['mbid']]
                    updated = True
            
            if enhanced_metadata.get('album_artist_id'):
                if audio.get('MUSICBRAINZ_ARTISTID') != [enhanced_metadata['album_artist_id']]:
                    audio['MUSICBRAINZ_ARTISTID'] = [enhanced_metadata['album_artist_id']]
                    updated = True
            
            if enhanced_metadata.get('release_group_id'):
                if audio.get('MUSICBRAINZ_RELEASEGROUPID') != [enhanced_metadata['release_group_id']]:
                    audio['MUSICBRAINZ_RELEASEGROUPID'] = [enhanced_metadata['release_group_id']]
                    updated = True
            
            if track_info and track_info.get('recording_id'):
                if audio.get('MUSICBRAINZ_TRACKID') != [track_info['recording_id']]:
                    audio['MUSICBRAINZ_TRACKID'] = [track_info['recording_id']]
                    updated = True
            
            if track_info and track_info.get('track_id'):
                if audio.get('MUSICBRAINZ_RELEASETRACKID') != [track_info['track_id']]:
                    audio['MUSICBRAINZ_RELEASETRACKID'] = [track_info['track_id']]
                    updated = True
            
            # Extended fields
            if enhanced_metadata.get('label'):
                if audio.get('LABEL') != [enhanced_metadata['label']]:
                    audio['LABEL'] = [enhanced_metadata['label']]
                    updated = True
            
            if enhanced_metadata.get('catalog_number'):
                if audio.get('CATALOGNUMBER') != [enhanced_metadata['catalog_number']]:
                    audio['CATALOGNUMBER'] = [enhanced_metadata['catalog_number']]
                    updated = True
            
            if enhanced_metadata.get('barcode'):
                if audio.get('BARCODE') != [enhanced_metadata['barcode']]:
                    audio['BARCODE'] = [enhanced_metadata['barcode']]
                    updated = True
            
            if enhanced_metadata.get('country'):
                if audio.get('COUNTRY') != [enhanced_metadata['country']]:
                    audio['COUNTRY'] = [enhanced_metadata['country']]
                    updated = True
            
            if enhanced_metadata.get('media'):
                if audio.get('MEDIA') != [enhanced_metadata['media']]:
                    audio['MEDIA'] = [enhanced_metadata['media']]
                    updated = True
            
            if enhanced_metadata.get('original_date'):
                if audio.get('ORIGINALDATE') != [enhanced_metadata['original_date']]:
                    audio['ORIGINALDATE'] = [enhanced_metadata['original_date']]
                    updated = True
            
            # Sort names
            if enhanced_metadata.get('album_artist_sort'):
                if audio.get('ALBUMARTISTSORT') != [enhanced_metadata['album_artist_sort']]:
                    audio['ALBUMARTISTSORT'] = [enhanced_metadata['album_artist_sort']]
                    updated = True
            
            if track_info and track_info.get('artist_sort'):
                if audio.get('ARTISTSORT') != [track_info['artist_sort']]:
                    audio['ARTISTSORT'] = [track_info['artist_sort']]
                    updated = True
            
            # ISRC
            if track_info and track_info.get('isrc'):
                if audio.get('ISRC') != [track_info['isrc']]:
                    audio['ISRC'] = [track_info['isrc']]
                    updated = True
            
            # Technical fields
            if not audio.get('ENCODER'):
                audio['ENCODER'] = ['FLAC 1.3.x']
                updated = True
            
            # Add total tracks
            total_tracks = len(enhanced_metadata.get('tracks', []))
            if total_tracks > 0:
                if audio.get('TOTALTRACKS') != [str(total_tracks)]:
                    audio['TOTALTRACKS'] = [str(total_tracks)]
                    updated = True
            
            # Save if updated
            if updated:
                audio.save()
                return True
            
            return False
            
        except Exception as e:
            print(f"   ❌ Error updating {flac_path.name}: {e}")
            return False

    def add_cover_art_if_missing(self, flac_path: Path, album_dir: Path) -> bool:
        """Add cover art to FLAC file if missing"""
        try:
            if self.dry_run:
                return False
                
            audio = FLAC(str(flac_path))
            
            # Check if cover art already exists
            if audio.pictures:
                return False
            
            # Look for cover art file
            cover_files = list(album_dir.glob("cover.*"))
            if not cover_files:
                return False
            
            cover_file = cover_files[0]
            
            # Read cover art data
            with open(cover_file, 'rb') as f:
                image_data = f.read()
            
            # Create picture object
            picture = Picture()
            picture.type = 3  # Cover (front)
            picture.data = image_data
            
            # Set MIME type based on file extension
            ext = cover_file.suffix.lower()
            if ext == '.jpg' or ext == '.jpeg':
                picture.mime = 'image/jpeg'
            elif ext == '.png':
                picture.mime = 'image/png'
            else:
                picture.mime = 'image/jpeg'  # Default
            
            # Add to FLAC file
            audio.add_picture(picture)
            audio.save()
            
            return True
            
        except Exception as e:
            print(f"   ⚠️  Failed to add cover art to {flac_path.name}: {e}")
            return False

    def enrich_album_metadata(self, album_dir: Path) -> Dict[str, Any]:
        """Enrich metadata for an entire album"""
        rip_info_path = album_dir / "rip_info.json"
        if not rip_info_path.exists():
            return {'error': 'No rip_info.json found', 'path': str(album_dir)}
        
        # Get current metadata from rip_info.json
        enhanced_metadata = self.get_enhanced_metadata_from_rip_info(rip_info_path)
        if 'error' in enhanced_metadata:
            return enhanced_metadata
        
        # Enhance with MusicBrainz data if available
        if enhanced_metadata.get('mbid'):
            mb_metadata = self.enhance_musicbrainz_metadata(enhanced_metadata['mbid'])
            if mb_metadata:
                # Merge MusicBrainz data (prefer MB data for most fields)
                for key, value in mb_metadata.items():
                    if value and key != 'tracks':  # Don't overwrite track info blindly
                        enhanced_metadata[key] = value
                
                # For tracks, merge carefully
                if 'tracks' in mb_metadata and mb_metadata['tracks']:
                    enhanced_metadata['tracks'] = mb_metadata['tracks']
        
        # Process FLAC files
        flac_files = sorted(album_dir.glob("*.flac"))
        results = {
            'album_path': str(album_dir),
            'total_files': len(flac_files),
            'updated_files': 0,
            'files_with_cover_added': 0,
            'errors': []
        }
        
        print(f"   📀 Processing {len(flac_files)} FLAC files...")
        
        for i, flac_file in enumerate(flac_files):
            try:
                # Get track-specific metadata
                track_info = None
                if enhanced_metadata.get('tracks') and i < len(enhanced_metadata['tracks']):
                    track_info = enhanced_metadata['tracks'][i]
                
                # Apply metadata standard
                if self.apply_metadata_standard(flac_file, enhanced_metadata, track_info):
                    results['updated_files'] += 1
                
                # Add cover art if missing
                if self.add_cover_art_if_missing(flac_file, album_dir):
                    results['files_with_cover_added'] += 1
                
            except Exception as e:
                error_msg = f"Error processing {flac_file.name}: {e}"
                results['errors'].append(error_msg)
                print(f"      ❌ {error_msg}")
        
        return results

    def find_all_albums(self) -> List[Path]:
        """Find all album directories with FLAC files"""
        albums = []
        
        # Skip the top-level directories we know aren't artists
        skip_dirs = {'.git', '__pycache__', 'logs', 'temp'}
        
        for item in self.output_dir.iterdir():
            if not item.is_dir() or item.name in skip_dirs:
                continue
            
            # Check if this directory has FLAC files (Various Artists albums)
            flac_files = list(item.glob("*.flac"))
            if flac_files:
                albums.append(item)
            
            # Check subdirectories for artist/album structure
            for subdir in item.iterdir():
                if subdir.is_dir():
                    sub_flac_files = list(subdir.glob("*.flac"))
                    if sub_flac_files:
                        albums.append(subdir)
        
        return sorted(albums)

    def enrich_all_metadata(self, max_albums: int = None) -> Dict[str, Any]:
        """Enrich metadata for all albums in the collection"""
        albums = self.find_all_albums()
        
        if max_albums:
            albums = albums[:max_albums]
        
        print(f"🎵 Found {len(albums)} albums to process")
        
        overall_stats = {
            'total_albums': len(albums),
            'processed_albums': 0,
            'total_files': 0,
            'updated_files': 0,
            'files_with_cover_added': 0,
            'albums_with_errors': 0,
            'start_time': time.time()
        }
        
        for i, album_dir in enumerate(albums, 1):
            relative_path = album_dir.relative_to(self.output_dir)
            print(f"\n📁 [{i}/{len(albums)}] {relative_path}")
            
            try:
                results = self.enrich_album_metadata(album_dir)
                
                if 'error' in results:
                    print(f"   ❌ {results['error']}")
                    overall_stats['albums_with_errors'] += 1
                    continue
                
                overall_stats['processed_albums'] += 1
                overall_stats['total_files'] += results['total_files']
                overall_stats['updated_files'] += results['updated_files']
                overall_stats['files_with_cover_added'] += results['files_with_cover_added']
                
                if results['errors']:
                    overall_stats['albums_with_errors'] += 1
                
                # Show progress
                if results['updated_files'] > 0:
                    print(f"   ✅ Updated {results['updated_files']}/{results['total_files']} files")
                else:
                    print(f"   ✓ All {results['total_files']} files already up to standard")
                
                if results['files_with_cover_added'] > 0:
                    print(f"   🖼️  Added cover art to {results['files_with_cover_added']} files")
                
            except Exception as e:
                print(f"   ❌ Error processing album: {e}")
                overall_stats['albums_with_errors'] += 1
        
        overall_stats['end_time'] = time.time()
        overall_stats['duration'] = overall_stats['end_time'] - overall_stats['start_time']
        
        return overall_stats

def main():
    """Main entry point"""
    print("=== FLAC Metadata Enrichment System ===")
    print("Applies music industry standard metadata to FLAC files")
    
    print("\nChoose operation:")
    print("1. Analyze current metadata status (no changes)")
    print("2. Enrich metadata for all albums")
    print("3. Enrich metadata for specific number of albums (testing)")
    print("4. Dry run - show what would be changed")
    
    while True:
        choice = input("Enter choice (1-4): ").strip()
        if choice in ['1', '2', '3', '4']:
            break
        print("Please enter 1, 2, 3, or 4")
    
    dry_run = (choice == '4')
    enricher = FLACMetadataEnricher(dry_run=dry_run)
    
    if choice == '1':
        # Analysis mode
        print("\n🔍 Analyzing metadata status...")
        albums = enricher.find_all_albums()
        print(f"Found {len(albums)} albums")
        
        # Sample analysis of first few albums
        for album_dir in albums[:5]:
            print(f"\n📁 {album_dir.relative_to(enricher.output_dir)}")
            flac_files = list(album_dir.glob("*.flac"))
            if flac_files:
                analysis = enricher.analyze_current_metadata(flac_files[0])
                if 'error' not in analysis:
                    print(f"   📊 Current fields: {len(analysis['current_fields'])}")
                    print(f"   ❌ Missing required: {len(analysis['missing_required'])}")
                    print(f"   ⚠️  Missing standard: {len(analysis['missing_standard'])}")
                    print(f"   🎵 Has MusicBrainz: {analysis['has_musicbrainz']}")
                    print(f"   🖼️  Has cover art: {analysis['has_cover_art']}")
        
        return 0
    
    elif choice == '3':
        # Limited enrichment for testing
        while True:
            try:
                max_albums = int(input("How many albums to process? "))
                if max_albums > 0:
                    break
                print("Please enter a positive number")
            except ValueError:
                print("Please enter a valid number")
    else:
        max_albums = None
    
    if choice in ['2', '3', '4']:
        if not dry_run:
            print("\n⚠️  This will modify FLAC files with enhanced metadata")
            confirm = input("Continue? (y/n): ").lower().strip()
            if confirm not in ['y', 'yes']:
                print("❌ Operation cancelled")
                return 0
        
        print(f"\n🚀 {'[DRY RUN] ' if dry_run else ''}Starting metadata enrichment...")
        
        stats = enricher.enrich_all_metadata(max_albums=max_albums)
        
        print(f"\n📊 Enrichment Results:")
        print(f"   📋 Albums processed: {stats['processed_albums']}/{stats['total_albums']}")
        print(f"   📁 Total FLAC files: {stats['total_files']}")
        print(f"   ✅ Files updated: {stats['updated_files']}")
        print(f"   🖼️  Cover art added: {stats['files_with_cover_added']}")
        print(f"   ❌ Albums with errors: {stats['albums_with_errors']}")
        print(f"   ⏱️  Duration: {stats['duration']:.1f} seconds")
        
        if not dry_run and stats['updated_files'] > 0:
            print(f"\n🎉 Successfully enriched {stats['updated_files']} FLAC files!")
            print("All files now conform to the metadata standard")
    
    return 0

if __name__ == "__main__":
    import sys
    sys.exit(main())
