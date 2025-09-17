#!/usr/bin/env python3
"""
FLAC Metadata Date Analyzer and Fixer

Analyzes date fields across FLAC collection to identify inconsistencies and provides
standardization according to Vorbis comment specifications.

FLAC Vorbis Comment Standards for Dates:
- DATE: Primary release date (YYYY-MM-DD preferred, YYYY acceptable)
- ORIGINALDATE: Original release date for reissues (YYYY-MM-DD preferred)
- YEAR: Deprecated in favor of DATE, but some players expect it

This tool:
1. Analyzes all date fields in the collection
2. Reports inconsistencies and missing dates
3. Standardizes dates to proper Vorbis format
4. Ensures compatibility with music players
"""

import os
import sys
import json
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Set
from mutagen.flac import FLAC
from collections import defaultdict, Counter
import argparse

class DateAnalyzer:
    def __init__(self, output_dir: str):
        self.output_dir = Path(output_dir)
        self.date_patterns = {
            'full_iso': re.compile(r'^\d{4}-\d{2}-\d{2}$'),           # 2023-05-15
            'year_month': re.compile(r'^\d{4}-\d{2}$'),              # 2023-05
            'year_only': re.compile(r'^\d{4}$'),                     # 2023
            'invalid_slash': re.compile(r'^\d{1,2}/\d{1,2}/\d{4}$'), # 5/15/2023
            'invalid_dot': re.compile(r'^\d{1,2}\.\d{1,2}\.\d{4}$'), # 15.5.2023
            'invalid_reverse': re.compile(r'^\d{2}/\d{2}/\d{4}$'),   # 15/05/2023
            'partial_year': re.compile(r'^\d{2,3}$'),                # 23, 023
        }
        
        self.stats = {
            'total_albums': 0,
            'total_tracks': 0,
            'date_formats': Counter(),
            'missing_dates': 0,
            'unknown_dates': 0,
            'invalid_formats': 0,
            'inconsistent_albums': [],
            'date_field_usage': Counter(),
            'problematic_albums': []
        }

    def analyze_date_format(self, date_value: str) -> Tuple[str, bool]:
        """Analyze date format and return type and validity"""
        if not date_value or date_value.lower() in ['unknown', 'n/a', '']:
            return 'missing', False
            
        date_value = date_value.strip()
        
        for format_name, pattern in self.date_patterns.items():
            if pattern.match(date_value):
                is_valid = format_name in ['full_iso', 'year_month', 'year_only']
                return format_name, is_valid
        
        return 'unrecognized', False

    def standardize_date(self, date_value: str, original_date: str = None) -> Optional[str]:
        """Convert date to standard ISO format"""
        if not date_value or date_value.lower() in ['unknown', 'n/a', '']:
            # If DATE is unknown but ORIGINALDATE exists, use ORIGINALDATE
            if original_date and original_date.lower() not in ['unknown', 'n/a', '']:
                return self.standardize_date(original_date)
            return None
            
        date_value = date_value.strip()
        
        # Already in correct format
        if self.date_patterns['full_iso'].match(date_value):
            return date_value
        if self.date_patterns['year_month'].match(date_value):
            return date_value  # Keep YYYY-MM format
        if self.date_patterns['year_only'].match(date_value):
            return date_value  # Keep YYYY format
            
        # Convert invalid formats
        if self.date_patterns['invalid_slash'].match(date_value):
            parts = date_value.split('/')
            if len(parts) == 3:
                month, day, year = parts
                return f"{year}-{month.zfill(2)}-{day.zfill(2)}"
                
        if self.date_patterns['invalid_dot'].match(date_value):
            parts = date_value.split('.')
            if len(parts) == 3:
                day, month, year = parts
                return f"{year}-{month.zfill(2)}-{day.zfill(2)}"
                
        if self.date_patterns['invalid_reverse'].match(date_value):
            parts = date_value.split('/')
            if len(parts) == 3:
                day, month, year = parts
                return f"{year}-{month.zfill(2)}-{day.zfill(2)}"
                
        # Handle partial years
        if self.date_patterns['partial_year'].match(date_value):
            if len(date_value) == 2:
                # Assume 2000s for now, could be made smarter
                return f"20{date_value}"
            elif len(date_value) == 3:
                # Handle 3-digit years (unlikely but possible)
                return f"1{date_value}"
                
        return None

    def analyze_album(self, album_dir: Path) -> Dict:
        """Analyze date metadata for a single album"""
        artist = album_dir.parent.name
        album = album_dir.name
        
        flac_files = list(album_dir.glob('*.flac'))
        if not flac_files:
            return None
            
        album_info = {
            'artist': artist,
            'album': album,
            'path': str(album_dir),
            'track_count': len(flac_files),
            'date_fields': {},
            'date_consistency': 'unknown',
            'issues': [],
            'recommendations': []
        }
        
        # Analyze each track
        date_values = defaultdict(set)
        field_usage = Counter()
        
        for flac_file in flac_files:
            try:
                audio = FLAC(flac_file)
                
                # Check all possible date fields
                date_fields = ['DATE', 'ORIGINALDATE', 'YEAR', 'RELEASEDATE']
                for field in date_fields:
                    if field in audio:
                        value = audio[field][0] if isinstance(audio[field], list) else audio[field]
                        date_values[field].add(value)
                        field_usage[field] += 1
                        
            except Exception as e:
                album_info['issues'].append(f"Error reading {flac_file.name}: {e}")
                
        # Analyze date consistency within album
        album_info['date_fields'] = {field: list(values) for field, values in date_values.items()}
        
        # Check for consistency issues
        for field, values in date_values.items():
            if len(values) > 1:
                album_info['issues'].append(f"Inconsistent {field} values: {list(values)}")
                album_info['date_consistency'] = 'inconsistent'
                
        # Analyze date formats and validity
        primary_date = None
        if 'DATE' in date_values:
            primary_date = list(date_values['DATE'])[0]
        elif 'YEAR' in date_values:
            primary_date = list(date_values['YEAR'])[0]
            
        if primary_date:
            format_type, is_valid = self.analyze_date_format(primary_date)
            album_info['primary_date'] = primary_date
            album_info['date_format'] = format_type
            album_info['date_valid'] = is_valid
            
            if not is_valid:
                # Check if we can use ORIGINALDATE when DATE is "Unknown"
                original_date = list(date_values.get('ORIGINALDATE', [None]))[0]
                standardized = self.standardize_date(primary_date, original_date)
                if standardized:
                    album_info['recommended_date'] = standardized
                    if original_date and primary_date.lower() in ['unknown', 'n/a']:
                        album_info['recommendations'].append(f"Use ORIGINALDATE '{original_date}' for DATE field (currently '{primary_date}')")
                    else:
                        album_info['recommendations'].append(f"Standardize date from '{primary_date}' to '{standardized}'")
                else:
                    album_info['recommendations'].append(f"Fix invalid date format: '{primary_date}'")
        else:
            # Check if ORIGINALDATE exists when DATE is missing
            original_date = list(date_values.get('ORIGINALDATE', [None]))[0]
            if original_date and original_date.lower() not in ['unknown', 'n/a']:
                standardized = self.standardize_date(original_date)
                if standardized:
                    album_info['recommended_date'] = standardized
                    album_info['recommendations'].append(f"Add DATE field using ORIGINALDATE value '{original_date}'")
                else:
                    album_info['issues'].append("No DATE or YEAR field found")
                    album_info['recommendations'].append("Add DATE field with release date")
            else:
                album_info['issues'].append("No DATE or YEAR field found")
                album_info['recommendations'].append("Add DATE field with release date")
            
        # Check for deprecated YEAR field usage
        if 'YEAR' in date_values and 'DATE' not in date_values:
            album_info['recommendations'].append("Replace YEAR field with DATE field (Vorbis standard)")
            
        # Update statistics
        self.stats['date_field_usage'].update(field_usage)
        if album_info.get('date_format'):
            self.stats['date_formats'][album_info['date_format']] += 1
            
        if album_info['issues']:
            self.stats['problematic_albums'].append(album_info)
            
        return album_info

    def analyze_collection(self) -> List[Dict]:
        """Analyze the entire collection for date metadata"""
        print("🔍 Analyzing date metadata across collection...")
        print("=" * 60)
        
        albums = []
        
        for artist_dir in self.output_dir.iterdir():
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
                    if not album_info.get('primary_date'):
                        self.stats['missing_dates'] += 1
                    elif album_info.get('primary_date', '').lower() in ['unknown', 'n/a']:
                        self.stats['unknown_dates'] += 1
                    elif not album_info.get('date_valid', True):
                        self.stats['invalid_formats'] += 1
                        
                    if album_info.get('date_consistency') == 'inconsistent':
                        self.stats['inconsistent_albums'].append(album_info)
        
        return albums

    def print_analysis_report(self, albums: List[Dict]):
        """Print comprehensive analysis report"""
        print(f"\n📊 Date Metadata Analysis Report")
        print("=" * 50)
        print(f"Total Albums: {self.stats['total_albums']}")
        print(f"Total Tracks: {self.stats['total_tracks']}")
        print(f"Albums with missing dates: {self.stats['missing_dates']}")
        print(f"Albums with 'Unknown' dates: {self.stats['unknown_dates']}")
        print(f"Albums with invalid date formats: {self.stats['invalid_formats']}")
        print(f"Albums with inconsistent dates: {len(self.stats['inconsistent_albums'])}")
        
        print(f"\n📅 Date Format Distribution:")
        for format_type, count in self.stats['date_formats'].most_common():
            percentage = (count / self.stats['total_albums']) * 100
            print(f"  {format_type}: {count} albums ({percentage:.1f}%)")
            
        print(f"\n🏷️  Date Field Usage:")
        for field, count in self.stats['date_field_usage'].most_common():
            print(f"  {field}: {count} tracks")
            
        # Show problematic albums
        if self.stats['problematic_albums']:
            print(f"\n⚠️  Albums with Date Issues ({len(self.stats['problematic_albums'])} albums):")
            for album in self.stats['problematic_albums'][:10]:  # Show first 10
                print(f"\n📁 {album['artist']} / {album['album']}")
                if album.get('primary_date'):
                    print(f"   Current date: {album['primary_date']} ({album.get('date_format', 'unknown')})")
                for issue in album['issues']:
                    print(f"   ⚠️  {issue}")
                for rec in album['recommendations']:
                    print(f"   💡 {rec}")
                    
            if len(self.stats['problematic_albums']) > 10:
                print(f"   ... and {len(self.stats['problematic_albums']) - 10} more albums")

    def fix_album_dates(self, album_info: Dict, dry_run: bool = True) -> bool:
        """Fix date metadata for a single album"""
        if not album_info.get('recommended_date'):
            return False
            
        album_path = Path(album_info['path'])
        flac_files = list(album_path.glob('*.flac'))
        
        if dry_run:
            print(f"Would fix: {album_info['artist']} / {album_info['album']}")
            current_date = album_info.get('primary_date', 'missing')
            print(f"  Change DATE from '{current_date}' to '{album_info['recommended_date']}'")
            return True
            
        fixed_count = 0
        for flac_file in flac_files:
            try:
                audio = FLAC(flac_file)
                
                # Set DATE field (primary)
                audio['DATE'] = album_info['recommended_date']
                
                # Remove deprecated YEAR field if it exists
                if 'YEAR' in audio:
                    del audio['YEAR']
                
                # Keep ORIGINALDATE field if it exists (it's valid metadata)
                # ORIGINALDATE should remain for reissues, remasters, etc.
                    
                audio.save()
                fixed_count += 1
                
            except Exception as e:
                print(f"Error fixing {flac_file}: {e}")
                
        if fixed_count > 0:
            print(f"✅ Fixed {fixed_count} tracks in {album_info['artist']} / {album_info['album']}")
            return True
            
        return False

    def batch_fix_dates(self, albums: List[Dict], dry_run: bool = True) -> int:
        """Fix date metadata for all problematic albums"""
        fixable_albums = [album for album in albums if album.get('recommended_date')]
        
        if not fixable_albums:
            print("No albums found that can be automatically fixed.")
            return 0
            
        print(f"\n🔧 {'Dry run' if dry_run else 'Fixing'} date metadata for {len(fixable_albums)} albums:")
        print("=" * 60)
        
        fixed_count = 0
        for album in fixable_albums:
            if self.fix_album_dates(album, dry_run):
                fixed_count += 1
                
        if dry_run:
            print(f"\n💡 Dry run complete. {fixed_count} albums can be fixed.")
            print("Run with --apply to make actual changes.")
        else:
            print(f"\n✅ Fixed date metadata for {fixed_count} albums.")
            
        return fixed_count

def main():
    parser = argparse.ArgumentParser(description="Analyze and fix FLAC date metadata")
    parser.add_argument('output_dir', nargs='?', default='output', help='Output directory to analyze')
    parser.add_argument('--apply', action='store_true', help='Apply fixes (default is dry run)')
    parser.add_argument('--export', help='Export analysis to JSON file')
    parser.add_argument('--show-all', action='store_true', help='Show all albums, not just problematic ones')
    
    args = parser.parse_args()
    
    if not os.path.exists(args.output_dir):
        print(f"❌ Output directory not found: {args.output_dir}")
        return 1
        
    analyzer = DateAnalyzer(args.output_dir)
    albums = analyzer.analyze_collection()
    
    # Print analysis report
    analyzer.print_analysis_report(albums)
    
    # Export analysis if requested
    if args.export:
        with open(args.export, 'w') as f:
            json.dump({
                'statistics': dict(analyzer.stats),
                'albums': albums
            }, f, indent=2, default=str)
        print(f"\n💾 Analysis exported to {args.export}")
    
    # Fix dates if there are issues to fix
    problematic_albums = [album for album in albums if album.get('recommendations')]
    if problematic_albums:
        print(f"\n🎯 Found {len(problematic_albums)} albums with date issues")
        
        if args.apply:
            response = input("\nApply date fixes? (y/N): ")
            if response.lower() == 'y':
                analyzer.batch_fix_dates(problematic_albums, dry_run=False)
            else:
                print("Fixes cancelled.")
        else:
            analyzer.batch_fix_dates(problematic_albums, dry_run=True)
    else:
        print("\n✅ All albums have consistent, valid date metadata!")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
