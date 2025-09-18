#!/usr/bin/env python3
"""
Multi-Disc Collection Scanner

Scans entire music collection to identify multi-disc albums and check their metadata status.
Uses the same logic as multi_disc_fixer.py to detect albums with X-YY filename patterns
and reports which ones have correct/incorrect DISCNUMBER metadata.

Usage:
    python3 scan_multidisc_collection.py "/path/to/output/directory"
    python3 scan_multidisc_collection.py "/path/to/output/directory" --fix-all
"""

import os
import sys
import re
import argparse
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from mutagen.flac import FLAC
from collections import defaultdict

class MultiDiscCollectionScanner:
    def __init__(self, output_path: str):
        self.output_path = Path(output_path)
        self.track_pattern = re.compile(r'^(\d+)-(\d+)\s+(.+)\.flac$')
        self.results = {
            'total_albums': 0,
            'multidisc_albums': 0,
            'albums_needing_fixes': 0,
            'albums_correct': 0,
            'albums_with_issues': []
        }
        
    def is_multidisc_album(self, album_path: Path) -> bool:
        """Check if album has multi-disc filename pattern"""
        flac_files = list(album_path.glob('*.flac'))
        if len(flac_files) < 2:
            return False
            
        disc_numbers = set()
        for flac_file in flac_files:
            match = self.track_pattern.match(flac_file.name)
            if match:
                disc_num = int(match.group(1))
                disc_numbers.add(disc_num)
            else:
                # If any file doesn't match pattern, not a standard multi-disc album
                return False
                
        # Multi-disc if we have more than one disc number
        return len(disc_numbers) > 1
    
    def analyze_multidisc_album(self, album_path: Path) -> Dict:
        """Analyze a multi-disc album for metadata issues"""
        tracks_by_disc = defaultdict(list)
        flac_files = list(album_path.glob('*.flac'))
        
        album_info = {
            'path': str(album_path),
            'name': album_path.name,
            'artist': album_path.parent.name,
            'total_tracks': len(flac_files),
            'discs': {},
            'has_issues': False,
            'issue_count': 0,
            'fixable': True
        }
        
        # Parse filenames and group by disc
        for flac_file in flac_files:
            match = self.track_pattern.match(flac_file.name)
            if not match:
                album_info['fixable'] = False
                continue
                
            disc_num = int(match.group(1))
            track_num = int(match.group(2))
            
            tracks_by_disc[disc_num].append({
                'file_path': flac_file,
                'disc_num': disc_num,
                'track_num': track_num,
                'filename': flac_file.name
            })
        
        # Check metadata for each disc
        for disc_num in sorted(tracks_by_disc.keys()):
            tracks = sorted(tracks_by_disc[disc_num], key=lambda x: x['track_num'])
            disc_issues = []
            
            for track in tracks:
                try:
                    audio = FLAC(track['file_path'])
                    current_disc = audio.get('DISCNUMBER', [None])[0]
                    current_track = audio.get('TRACKNUMBER', [None])[0]
                    
                    # Check DISCNUMBER
                    if current_disc != str(disc_num):
                        disc_issues.append({
                            'track': track['filename'],
                            'issue': f"DISCNUMBER is '{current_disc}', should be '{disc_num}'"
                        })
                        
                    # Check TRACKNUMBER format
                    expected_track = f"{track['track_num']:02d}"
                    if current_track and current_track != expected_track:
                        if current_track.startswith(f"{disc_num}-"):
                            disc_issues.append({
                                'track': track['filename'],
                                'issue': f"TRACKNUMBER has disc prefix '{current_track}', should be '{expected_track}'"
                            })
                        else:
                            disc_issues.append({
                                'track': track['filename'],
                                'issue': f"TRACKNUMBER is '{current_track}', should be '{expected_track}'"
                            })
                            
                except Exception as e:
                    disc_issues.append({
                        'track': track['filename'],
                        'issue': f"Error reading metadata: {e}"
                    })
            
            album_info['discs'][disc_num] = {
                'track_count': len(tracks),
                'issues': disc_issues
            }
            
            if disc_issues:
                album_info['has_issues'] = True
                album_info['issue_count'] += len(disc_issues)
        
        album_info['total_discs'] = len(tracks_by_disc)
        return album_info
    
    def scan_collection(self) -> Dict:
        """Scan entire collection for multi-disc albums"""
        print(f"🔍 Scanning collection for multi-disc albums...")
        print(f"📁 Collection path: {self.output_path}")
        print("=" * 80)
        
        if not self.output_path.exists():
            print(f"❌ Collection directory not found: {self.output_path}")
            return self.results
        
        # Walk through all artist directories
        for artist_dir in self.output_path.iterdir():
            if not artist_dir.is_dir():
                continue
                
            # Walk through all album directories for this artist
            for album_dir in artist_dir.iterdir():
                if not album_dir.is_dir():
                    continue
                    
                self.results['total_albums'] += 1
                
                # Check if this is a multi-disc album
                if self.is_multidisc_album(album_dir):
                    self.results['multidisc_albums'] += 1
                    print(f"📀 Found multi-disc: {artist_dir.name} / {album_dir.name}")
                    
                    # Analyze the album
                    album_info = self.analyze_multidisc_album(album_dir)
                    
                    if album_info['has_issues']:
                        self.results['albums_needing_fixes'] += 1
                        self.results['albums_with_issues'].append(album_info)
                        print(f"   ⚠️  {album_info['issue_count']} metadata issues found")
                    else:
                        self.results['albums_correct'] += 1
                        print(f"   ✅ Metadata correct")
        
        return self.results
    
    def print_summary_report(self):
        """Print summary of collection scan"""
        print("\n" + "=" * 80)
        print("📊 MULTI-DISC COLLECTION SCAN SUMMARY")
        print("=" * 80)
        print(f"📁 Total Albums Scanned: {self.results['total_albums']}")
        print(f"💿 Multi-Disc Albums Found: {self.results['multidisc_albums']}")
        print(f"✅ Albums with Correct Metadata: {self.results['albums_correct']}")
        print(f"⚠️  Albums Needing Fixes: {self.results['albums_needing_fixes']}")
        
        if self.results['albums_with_issues']:
            print(f"\n🔧 ALBUMS REQUIRING METADATA FIXES:")
            print("-" * 80)
            
            for album in self.results['albums_with_issues']:
                print(f"\n📀 {album['artist']} / {album['name']}")
                print(f"   📁 Path: {album['path']}")
                print(f"   💿 Discs: {album['total_discs']}, Tracks: {album['total_tracks']}")
                print(f"   ⚠️  Issues: {album['issue_count']}")
                
                # Show disc-by-disc breakdown
                for disc_num in sorted(album['discs'].keys()):
                    disc_info = album['discs'][disc_num]
                    if disc_info['issues']:
                        print(f"      💿 Disc {disc_num}: {len(disc_info['issues'])} issues")
                        for issue in disc_info['issues'][:3]:  # Show first 3 issues
                            print(f"         - {issue['issue']}")
                        if len(disc_info['issues']) > 3:
                            print(f"         - ... and {len(disc_info['issues']) - 3} more")
            
            print(f"\n💡 To fix these albums, run:")
            print(f"   python cd_manager.py fix-multidisc \"<album_path>\" --apply")
            print(f"\n   Or use --fix-all to fix all albums automatically")
        else:
            print(f"\n🎉 All multi-disc albums have correct metadata!")
    
    def fix_all_albums(self):
        """Fix all albums with metadata issues"""
        if not self.results['albums_with_issues']:
            print("✅ No albums need fixing!")
            return 0
            
        print(f"\n🔧 FIXING ALL {len(self.results['albums_with_issues'])} ALBUMS WITH ISSUES")
        print("=" * 80)
        
        # Import the MultiDiscFixer class
        sys.path.append(str(Path(__file__).parent))
        from multi_disc_fixer import MultiDiscFixer
        
        fixed_albums = 0
        for album in self.results['albums_with_issues']:
            print(f"\n📀 Fixing: {album['artist']} / {album['name']}")
            
            try:
                fixer = MultiDiscFixer(album['path'])
                album_info = fixer.analyze_album()
                
                if album_info and album_info.get('fixable'):
                    fixes_made = fixer.fix_album_metadata(album_info, dry_run=False)
                    if fixes_made > 0:
                        fixed_albums += 1
                        print(f"   ✅ Fixed {fixes_made} tracks")
                    else:
                        print(f"   ✅ No fixes needed")
                else:
                    print(f"   ❌ Album not fixable automatically")
                    
            except Exception as e:
                print(f"   ❌ Error fixing album: {e}")
        
        print(f"\n🎉 Fixed metadata for {fixed_albums} albums!")
        return fixed_albums

def main():
    parser = argparse.ArgumentParser(description="Scan collection for multi-disc albums needing metadata fixes")
    parser.add_argument('output_path', help='Path to music collection output directory')
    parser.add_argument('--fix-all', action='store_true', help='Automatically fix all albums with issues')
    
    args = parser.parse_args()
    
    if not os.path.exists(args.output_path):
        print(f"❌ Output directory not found: {args.output_path}")
        return 1
        
    if not os.path.isdir(args.output_path):
        print(f"❌ Path is not a directory: {args.output_path}")
        return 1
    
    scanner = MultiDiscCollectionScanner(args.output_path)
    results = scanner.scan_collection()
    scanner.print_summary_report()
    
    if args.fix_all:
        scanner.fix_all_albums()
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
