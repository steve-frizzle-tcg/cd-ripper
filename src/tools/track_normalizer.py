#!/usr/bin/env python3
"""
Collection-Wide Track Number Normalizer

Fixes TRACKNUMBER format across the entire collection to comply with FLAC Vorbis comment standards.

The current collection uses disc-track format (01-01, 01-02, etc.) for all albums,
but proper Vorbis comment standards require:
- TRACKNUMBER: Simple track number (01, 02, 03, etc.)  
- DISCNUMBER: Disc number for multi-disc albums (1, 2, etc.)

This tool:
1. Scans the entire collection for TRACKNUMBER format issues
2. Converts disc-track format (01-03) to simple format (03)
3. Sets proper DISCNUMBER field for multi-disc albums
4. Maintains single-disc albums with DISCNUMBER=1
5. Updates metadata to proper Vorbis comment standards

Usage:
    python3 track_normalizer.py output                 # Analyze entire collection
    python3 track_normalizer.py output --apply         # Fix entire collection
    python3 track_normalizer.py "path/to/album" --apply # Fix single album
"""

import os
import sys
import re
import argparse
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from mutagen.flac import FLAC
from collections import defaultdict

class TrackNumberNormalizer:
    def __init__(self):
        self.disc_track_pattern = re.compile(r'^(\d+)-(\d+)$')  # Matches 01-03
        self.simple_track_pattern = re.compile(r'^\d+$')        # Matches 03
        self.stats = {
            'total_albums': 0,
            'total_tracks': 0,
            'albums_with_issues': 0,
            'tracks_fixed': 0,
            'format_types': defaultdict(int)
        }
        
    def analyze_track_format(self, tracknumber: str) -> Tuple[str, Optional[int], Optional[int]]:
        """Analyze track number format and extract components"""
        if not tracknumber:
            return 'missing', None, None
            
        # Check for disc-track format (01-03)
        disc_match = self.disc_track_pattern.match(tracknumber)
        if disc_match:
            disc_num = int(disc_match.group(1))
            track_num = int(disc_match.group(2))
            return 'disc-track', disc_num, track_num
            
        # Check for simple format (03)
        if self.simple_track_pattern.match(tracknumber):
            return 'simple', None, int(tracknumber)
            
        return 'invalid', None, None
    
    def analyze_album(self, album_path: Path) -> Dict:
        """Analyze track number format for a single album"""
        flac_files = list(album_path.glob('*.flac'))
        if not flac_files:
            return None
            
        album_info = {
            'album_path': str(album_path),
            'artist': album_path.parent.name,
            'album': album_path.name,
            'track_count': len(flac_files),
            'issues': [],
            'tracks': [],
            'needs_fix': False,
            'is_multidisc': False
        }
        
        disc_numbers = set()
        track_formats = defaultdict(int)
        
        for flac_file in sorted(flac_files):
            try:
                audio = FLAC(flac_file)
                current_tracknumber = audio.get('TRACKNUMBER', [None])[0]
                current_discnumber = audio.get('DISCNUMBER', [None])[0]
                
                format_type, extracted_disc, extracted_track = self.analyze_track_format(current_tracknumber)
                track_formats[format_type] += 1
                
                track_info = {
                    'filename': flac_file.name,
                    'current_tracknumber': current_tracknumber,
                    'current_discnumber': current_discnumber,
                    'format_type': format_type,
                    'extracted_disc': extracted_disc,
                    'extracted_track': extracted_track,
                    'needs_fix': False,
                    'recommended_tracknumber': None,
                    'recommended_discnumber': None
                }
                
                # Determine if fixes are needed
                if format_type == 'disc-track':
                    track_info['needs_fix'] = True
                    track_info['recommended_tracknumber'] = f"{extracted_track:02d}"
                    track_info['recommended_discnumber'] = str(extracted_disc)
                    album_info['needs_fix'] = True
                    
                    if extracted_disc > 1:
                        album_info['is_multidisc'] = True
                        
                elif format_type == 'simple':
                    # Check if DISCNUMBER is missing or incorrect
                    if not current_discnumber:
                        track_info['needs_fix'] = True
                        track_info['recommended_discnumber'] = "1"
                        album_info['needs_fix'] = True
                        
                elif format_type in ['missing', 'invalid']:
                    album_info['issues'].append(f"Invalid TRACKNUMBER format: {current_tracknumber}")
                    
                if current_discnumber:
                    disc_numbers.add(int(current_discnumber))
                    
                album_info['tracks'].append(track_info)
                
            except Exception as e:
                album_info['issues'].append(f"Error reading {flac_file.name}: {e}")
                
        # Determine if album is multi-disc
        if len(disc_numbers) > 1 or any(d > 1 for d in disc_numbers):
            album_info['is_multidisc'] = True
            
        album_info['format_distribution'] = dict(track_formats)
        
        return album_info
    
    def analyze_collection(self, collection_path: Path) -> List[Dict]:
        """Analyze track number formats across entire collection"""
        print("🔍 Analyzing track number formats across collection...")
        print("=" * 70)
        
        albums = []
        
        for artist_dir in collection_path.iterdir():
            if not artist_dir.is_dir():
                continue
                
            for album_dir in artist_dir.iterdir():
                if not album_dir.is_dir():
                    continue
                    
                self.stats['total_albums'] += 1
                album_info = self.analyze_album(album_dir)
                
                if album_info:
                    albums.append(album_info)
                    self.stats['total_tracks'] += album_info['track_count']
                    
                    # Update statistics
                    for format_type, count in album_info['format_distribution'].items():
                        self.stats['format_types'][format_type] += count
                        
                    if album_info['needs_fix']:
                        self.stats['albums_with_issues'] += 1
                        
        return albums
    
    def print_analysis_report(self, albums: List[Dict]):
        """Print comprehensive analysis report"""
        print(f"\n📊 Track Number Format Analysis Report")
        print("=" * 50)
        print(f"Total Albums: {self.stats['total_albums']}")
        print(f"Total Tracks: {self.stats['total_tracks']}")
        print(f"Albums needing fixes: {self.stats['albums_with_issues']}")
        
        print(f"\n📅 Track Number Format Distribution:")
        for format_type, count in self.stats['format_types'].items():
            percentage = (count / self.stats['total_tracks']) * 100
            icon = "❌" if format_type in ['disc-track', 'missing', 'invalid'] else "✅"
            print(f"  {icon} {format_type}: {count} tracks ({percentage:.1f}%)")
            
        # Show problematic albums sample
        problem_albums = [album for album in albums if album['needs_fix']]
        if problem_albums:
            print(f"\n⚠️  Sample Albums with Track Number Issues:")
            for album in problem_albums[:5]:  # Show first 5
                print(f"\n📁 {album['artist']} / {album['album']}")
                print(f"   Format distribution: {album['format_distribution']}")
                if album['is_multidisc']:
                    print(f"   💿 Multi-disc album detected")
                    
                for track in album['tracks'][:3]:  # Show first 3 tracks
                    if track['needs_fix']:
                        print(f"   🔧 {track['filename']}: {track['current_tracknumber']} → {track['recommended_tracknumber']}")
                        
            if len(problem_albums) > 5:
                print(f"   ... and {len(problem_albums) - 5} more albums")
    
    def fix_album_tracks(self, album_info: Dict, dry_run: bool = True) -> int:
        """Fix track numbers for a single album"""
        if not album_info['needs_fix']:
            return 0
            
        fixed_count = 0
        
        if dry_run:
            print(f"\n📁 Would fix: {album_info['artist']} / {album_info['album']}")
        else:
            print(f"\n📁 Fixing: {album_info['artist']} / {album_info['album']}")
            
        for track in album_info['tracks']:
            if not track['needs_fix']:
                continue
                
            if dry_run:
                changes = []
                if track['recommended_tracknumber']:
                    changes.append(f"TRACKNUMBER: {track['current_tracknumber']} → {track['recommended_tracknumber']}")
                if track['recommended_discnumber'] and track['current_discnumber'] != track['recommended_discnumber']:
                    changes.append(f"DISCNUMBER: {track['current_discnumber']} → {track['recommended_discnumber']}")
                    
                if changes:
                    print(f"   Would fix {track['filename']}: {', '.join(changes)}")
                    fixed_count += 1
            else:
                try:
                    flac_path = Path(album_info['album_path']) / track['filename']
                    audio = FLAC(flac_path)
                    
                    changes_made = False
                    
                    # Fix TRACKNUMBER
                    if track['recommended_tracknumber']:
                        audio['TRACKNUMBER'] = track['recommended_tracknumber']
                        changes_made = True
                        
                    # Fix DISCNUMBER
                    if track['recommended_discnumber'] and track['current_discnumber'] != track['recommended_discnumber']:
                        audio['DISCNUMBER'] = track['recommended_discnumber']
                        changes_made = True
                        
                    if changes_made:
                        audio.save()
                        fixed_count += 1
                        
                except Exception as e:
                    print(f"   ❌ Error fixing {track['filename']}: {e}")
                    
        if not dry_run and fixed_count > 0:
            print(f"   ✅ Fixed {fixed_count} tracks")
            
        return fixed_count
    
    def fix_collection(self, albums: List[Dict], dry_run: bool = True) -> int:
        """Fix track numbers for entire collection"""
        problem_albums = [album for album in albums if album['needs_fix']]
        
        if not problem_albums:
            print("✅ All albums already have correct track number format!")
            return 0
            
        print(f"\n🔧 {'Dry run' if dry_run else 'Fixing'} track number format for {len(problem_albums)} albums:")
        print("=" * 70)
        
        total_fixed = 0
        for album in problem_albums:
            fixed_count = self.fix_album_tracks(album, dry_run)
            total_fixed += fixed_count
            
        if dry_run and total_fixed > 0:
            print(f"\n💡 Dry run complete. {total_fixed} tracks would be fixed across {len(problem_albums)} albums.")
            print("Add --apply to make actual changes.")
        elif not dry_run and total_fixed > 0:
            print(f"\n✅ Fixed {total_fixed} tracks across {len(problem_albums)} albums")
            
        return total_fixed

def main():
    parser = argparse.ArgumentParser(description="Normalize track numbers across collection")
    parser.add_argument('path', help='Path to collection or single album')
    parser.add_argument('--apply', action='store_true', help='Apply fixes (default is dry run)')
    
    args = parser.parse_args()
    
    if not os.path.exists(args.path):
        print(f"❌ Path not found: {args.path}")
        return 1
        
    path = Path(args.path)
    normalizer = TrackNumberNormalizer()
    
    if path.is_file() or (path.is_dir() and list(path.glob('*.flac'))):
        # Single album
        album_info = normalizer.analyze_album(path)
        if album_info:
            print(f"📁 Analyzing album: {album_info['artist']} / {album_info['album']}")
            print("=" * 50)
            
            if album_info['needs_fix']:
                if args.apply:
                    response = input(f"\nApply track number fixes? (y/N): ")
                    if response.lower() == 'y':
                        normalizer.fix_album_tracks(album_info, dry_run=False)
                    else:
                        print("Fixes cancelled.")
                else:
                    normalizer.fix_album_tracks(album_info, dry_run=True)
            else:
                print("✅ Album already has correct track number format!")
        else:
            print("❌ No FLAC files found in album directory")
    else:
        # Entire collection
        albums = normalizer.analyze_collection(path)
        normalizer.print_analysis_report(albums)
        
        # Fix collection
        problem_albums = [album for album in albums if album['needs_fix']]
        if problem_albums:
            if args.apply:
                response = input(f"\nApply track number fixes to {len(problem_albums)} albums? (y/N): ")
                if response.lower() == 'y':
                    normalizer.fix_collection(albums, dry_run=False)
                else:
                    print("Fixes cancelled.")
            else:
                normalizer.fix_collection(albums, dry_run=True)
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
