#!/usr/bin/env python3
"""
Multi-Disc Album Metadata Corrector

Fixes DISCNUMBER and TRACKNUMBER metadata for multi-disc albums where:
1. File names follow the pattern: X-YY Track Name.flac (disc-track format)
2. DISCNUMBER metadata is missing or incorrect
3. TRACKNUMBER metadata may include disc prefix

This tool:
- Parses disc and track numbers from filenames
- Sets correct DISCNUMBER field for each track
- Normalizes TRACKNUMBER field (removes disc prefix if present)
- Updates TOTALDISCS field if needed
- Maintains all other metadata intact

Usage:
    python3 multi_disc_fixer.py "/path/to/album/directory"
    python3 multi_disc_fixer.py "/path/to/album/directory" --apply
"""

import os
import sys
import re
import argparse
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from mutagen.flac import FLAC
from collections import defaultdict

class MultiDiscFixer:
    def __init__(self, album_path: str):
        self.album_path = Path(album_path)
        self.track_pattern = re.compile(r'^(\d+)-(\d+)\s+(.+)\.flac$')
        self.tracks_by_disc = defaultdict(list)
        self.issues = []
        
    def analyze_album(self) -> Dict:
        """Analyze the album structure and identify disc/track issues"""
        print(f"🔍 Analyzing multi-disc album: {self.album_path.name}")
        print("=" * 60)
        
        flac_files = list(self.album_path.glob('*.flac'))
        if not flac_files:
            print("❌ No FLAC files found in directory")
            return {}
            
        album_info = {
            'album_path': str(self.album_path),
            'total_tracks': len(flac_files),
            'discs': {},
            'issues': [],
            'fixable': True
        }
        
        # Parse filenames to extract disc/track structure
        for flac_file in flac_files:
            match = self.track_pattern.match(flac_file.name)
            if not match:
                self.issues.append(f"Filename doesn't match pattern: {flac_file.name}")
                album_info['fixable'] = False
                continue
                
            disc_num = int(match.group(1))
            track_num = int(match.group(2))
            title = match.group(3)
            
            self.tracks_by_disc[disc_num].append({
                'file_path': flac_file,
                'disc_num': disc_num,
                'track_num': track_num,
                'title': title,
                'filename': flac_file.name
            })
        
        # Analyze each disc
        for disc_num in sorted(self.tracks_by_disc.keys()):
            tracks = sorted(self.tracks_by_disc[disc_num], key=lambda x: x['track_num'])
            album_info['discs'][disc_num] = {
                'track_count': len(tracks),
                'tracks': tracks,
                'issues': []
            }
            
            # Check metadata for each track
            for track in tracks:
                try:
                    audio = FLAC(track['file_path'])
                    current_disc = audio.get('DISCNUMBER', [None])[0]
                    current_track = audio.get('TRACKNUMBER', [None])[0]
                    
                    track['current_discnumber'] = current_disc
                    track['current_tracknumber'] = current_track
                    track['expected_discnumber'] = str(disc_num)
                    track['expected_tracknumber'] = f"{track['track_num']:02d}"
                    
                    # Check for issues
                    if current_disc != str(disc_num):
                        issue = f"Disc {disc_num} Track {track['track_num']:02d}: DISCNUMBER is '{current_disc}', should be '{disc_num}'"
                        album_info['discs'][disc_num]['issues'].append(issue)
                        
                    if current_track and current_track != f"{track['track_num']:02d}":
                        # Check if it has disc prefix
                        if current_track.startswith(f"{disc_num}-"):
                            issue = f"Disc {disc_num} Track {track['track_num']:02d}: TRACKNUMBER has disc prefix '{current_track}', should be '{track['track_num']:02d}'"
                        else:
                            issue = f"Disc {disc_num} Track {track['track_num']:02d}: TRACKNUMBER is '{current_track}', should be '{track['track_num']:02d}'"
                        album_info['discs'][disc_num]['issues'].append(issue)
                        
                except Exception as e:
                    issue = f"Error reading {track['filename']}: {e}"
                    album_info['discs'][disc_num]['issues'].append(issue)
                    
        album_info['total_discs'] = len(self.tracks_by_disc)
        album_info['issues'] = self.issues
        
        return album_info
    
    def print_analysis_report(self, album_info: Dict):
        """Print detailed analysis report"""
        print(f"📀 Album: {self.album_path.name}")
        print(f"📁 Path: {album_info['album_path']}")
        print(f"💿 Total Discs: {album_info['total_discs']}")
        print(f"🎵 Total Tracks: {album_info['total_tracks']}")
        
        if not album_info['fixable']:
            print("❌ Album cannot be automatically fixed:")
            for issue in album_info['issues']:
                print(f"   ⚠️  {issue}")
            return
            
        has_issues = False
        for disc_num in sorted(album_info['discs'].keys()):
            disc_info = album_info['discs'][disc_num]
            print(f"\n💿 Disc {disc_num}: {disc_info['track_count']} tracks")
            
            if disc_info['issues']:
                has_issues = True
                for issue in disc_info['issues']:
                    print(f"   ⚠️  {issue}")
            else:
                print(f"   ✅ All metadata correct")
                
        if not has_issues:
            print("\n✅ All disc metadata is correct!")
        else:
            print(f"\n🎯 Found metadata issues that can be fixed")
    
    def fix_track_metadata(self, track_info: Dict, dry_run: bool = True) -> bool:
        """Fix metadata for a single track"""
        try:
            if dry_run:
                changes = []
                if track_info['current_discnumber'] != track_info['expected_discnumber']:
                    changes.append(f"DISCNUMBER: '{track_info['current_discnumber']}' → '{track_info['expected_discnumber']}'")
                if track_info['current_tracknumber'] != track_info['expected_tracknumber']:
                    changes.append(f"TRACKNUMBER: '{track_info['current_tracknumber']}' → '{track_info['expected_tracknumber']}'")
                
                if changes:
                    print(f"   Would fix {track_info['filename']}: {', '.join(changes)}")
                return len(changes) > 0
            else:
                audio = FLAC(track_info['file_path'])
                changes_made = False
                
                # Fix DISCNUMBER
                if track_info['current_discnumber'] != track_info['expected_discnumber']:
                    audio['DISCNUMBER'] = track_info['expected_discnumber']
                    changes_made = True
                    
                # Fix TRACKNUMBER  
                if track_info['current_tracknumber'] != track_info['expected_tracknumber']:
                    audio['TRACKNUMBER'] = track_info['expected_tracknumber']
                    changes_made = True
                
                if changes_made:
                    audio.save()
                    print(f"   ✅ Fixed {track_info['filename']}")
                    
                return changes_made
                
        except Exception as e:
            print(f"   ❌ Error fixing {track_info['filename']}: {e}")
            return False
    
    def fix_album_metadata(self, album_info: Dict, dry_run: bool = True) -> int:
        """Fix metadata for entire album"""
        if not album_info['fixable']:
            print("❌ Album cannot be automatically fixed")
            return 0
            
        print(f"\n🔧 {'Dry run' if dry_run else 'Fixing'} multi-disc metadata:")
        print("=" * 60)
        
        fixed_count = 0
        for disc_num in sorted(album_info['discs'].keys()):
            disc_info = album_info['discs'][disc_num]
            
            if not disc_info['issues']:
                continue
                
            print(f"\n💿 Disc {disc_num}:")
            
            for track in disc_info['tracks']:
                needs_fix = (track['current_discnumber'] != track['expected_discnumber'] or 
                           track['current_tracknumber'] != track['expected_tracknumber'])
                
                if needs_fix:
                    if self.fix_track_metadata(track, dry_run):
                        fixed_count += 1
        
        # Update TOTALDISCS if needed (check first track of first disc)
        if album_info['discs'] and not dry_run:
            first_disc = min(album_info['discs'].keys())
            first_track = album_info['discs'][first_disc]['tracks'][0]
            
            try:
                audio = FLAC(first_track['file_path'])
                current_total = audio.get('TOTALDISCS', [None])[0]
                expected_total = str(album_info['total_discs'])
                
                if current_total != expected_total:
                    # Update TOTALDISCS in all tracks
                    for disc_num in album_info['discs'].keys():
                        for track in album_info['discs'][disc_num]['tracks']:
                            try:
                                track_audio = FLAC(track['file_path'])
                                track_audio['TOTALDISCS'] = expected_total
                                track_audio.save()
                            except Exception as e:
                                print(f"   ⚠️  Could not update TOTALDISCS in {track['filename']}: {e}")
                    
                    print(f"   ✅ Updated TOTALDISCS to {expected_total}")
                    
            except Exception as e:
                print(f"   ⚠️  Could not check TOTALDISCS: {e}")
        
        if dry_run and fixed_count > 0:
            print(f"\n💡 Dry run complete. {fixed_count} tracks need fixes.")
            print("Add --apply to make actual changes.")
        elif not dry_run and fixed_count > 0:
            print(f"\n✅ Fixed metadata for {fixed_count} tracks")
        elif fixed_count == 0:
            print(f"\n✅ No metadata fixes needed")
            
        return fixed_count

def main():
    parser = argparse.ArgumentParser(description="Fix multi-disc album metadata")
    parser.add_argument('album_path', help='Path to album directory')
    parser.add_argument('--apply', action='store_true', help='Apply fixes (default is dry run)')
    
    args = parser.parse_args()
    
    if not os.path.exists(args.album_path):
        print(f"❌ Album directory not found: {args.album_path}")
        return 1
        
    if not os.path.isdir(args.album_path):
        print(f"❌ Path is not a directory: {args.album_path}")
        return 1
    
    fixer = MultiDiscFixer(args.album_path)
    album_info = fixer.analyze_album()
    
    if not album_info:
        return 1
        
    # Print analysis report
    fixer.print_analysis_report(album_info)
    
    # Fix metadata if issues found
    has_issues = any(disc['issues'] for disc in album_info['discs'].values())
    
    if has_issues and album_info['fixable']:
        if args.apply:
            response = input(f"\nApply metadata fixes? (y/N): ")
            if response.lower() == 'y':
                fixer.fix_album_metadata(album_info, dry_run=False)
            else:
                print("Fixes cancelled.")
        else:
            fixer.fix_album_metadata(album_info, dry_run=True)
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
