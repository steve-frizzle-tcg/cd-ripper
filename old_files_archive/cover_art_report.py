#!/usr/bin/env python3
"""
Cover Art Status Report
Provides comprehensive analysis of cover art status across the music collection.
"""

import os
import sys
import json
from pathlib import Path
from typing import Dict, List, Tuple
from mutagen.flac import FLAC
from PIL import Image

class CoverArtAnalyzer:
    """Analyzes cover art status across the collection"""
    
    def __init__(self):
        self.stats = {
            'total_albums': 0,
            'albums_with_files': 0,
            'albums_with_flac_art': 0,
            'albums_with_both': 0,
            'albums_missing_all': 0,
            'albums_file_only': 0,
            'albums_flac_only': 0,
            'image_sizes': [],
            'file_formats': {},
            'issues': []
        }
    
    def analyze_album(self, album_dir: Path) -> Dict:
        """Analyze cover art status for a single album"""
        artist = album_dir.parent.name
        album = album_dir.name
        
        # Check for cover art files
        cover_files = (list(album_dir.glob('cover.*')) + 
                      list(album_dir.glob('folder.*')) +
                      list(album_dir.glob('*.jpg')) + 
                      list(album_dir.glob('*.jpeg')) + 
                      list(album_dir.glob('*.png')))
        
        # Remove duplicate paths and non-image files
        cover_files = list(set(cover_files))
        cover_files = [f for f in cover_files if f.suffix.lower() in ['.jpg', '.jpeg', '.png']]
        
        # Check FLAC files for embedded art
        flac_files = list(album_dir.glob('*.flac'))
        flac_with_art = 0
        flac_without_art = 0
        
        for flac_path in flac_files:
            try:
                audio = FLAC(flac_path)
                if audio.pictures:
                    flac_with_art += 1
                else:
                    flac_without_art += 1
            except Exception:
                continue
        
        # Analyze cover file quality if present
        cover_info = None
        if cover_files:
            cover_file = cover_files[0]  # Use first found
            try:
                with Image.open(cover_file) as img:
                    width, height = img.size
                    format_name = img.format
                    file_size = cover_file.stat().st_size
                    
                    cover_info = {
                        'file': cover_file.name,
                        'format': format_name,
                        'dimensions': f"{width}x{height}",
                        'size_kb': round(file_size / 1024, 1),
                        'quality': self.assess_quality(width, height, file_size)
                    }
                    
                    self.stats['image_sizes'].append((width, height))
                    self.stats['file_formats'][format_name] = self.stats['file_formats'].get(format_name, 0) + 1
                    
            except Exception as e:
                cover_info = {'error': str(e)}
        
        return {
            'artist': artist,
            'album': album,
            'path': str(album_dir),
            'cover_files': len(cover_files),
            'cover_info': cover_info,
            'flac_files': len(flac_files),
            'flac_with_art': flac_with_art,
            'flac_without_art': flac_without_art,
            'has_file_art': len(cover_files) > 0,
            'has_flac_art': flac_with_art > 0,
            'all_flac_have_art': flac_without_art == 0 and flac_with_art > 0
        }
    
    def assess_quality(self, width: int, height: int, file_size: int) -> str:
        """Assess cover art quality"""
        min_dimension = min(width, height)
        
        if min_dimension >= 800 and file_size >= 100000:  # 100KB+
            return "Excellent"
        elif min_dimension >= 600 and file_size >= 50000:  # 50KB+
            return "Good"
        elif min_dimension >= 400:
            return "Fair"
        elif min_dimension >= 200:
            return "Poor"
        else:
            return "Very Poor"
    
    def analyze_collection(self, output_dir: Path) -> List[Dict]:
        """Analyze the entire collection"""
        albums = []
        
        print("🔍 Analyzing cover art across collection...")
        
        for artist_dir in output_dir.iterdir():
            if not artist_dir.is_dir():
                continue
                
            for album_dir in artist_dir.iterdir():
                if not album_dir.is_dir():
                    continue
                
                self.stats['total_albums'] += 1
                album_info = self.analyze_album(album_dir)
                albums.append(album_info)
                
                # Update statistics
                if album_info['has_file_art']:
                    self.stats['albums_with_files'] += 1
                    
                if album_info['has_flac_art']:
                    self.stats['albums_with_flac_art'] += 1
                
                if album_info['has_file_art'] and album_info['has_flac_art']:
                    self.stats['albums_with_both'] += 1
                elif album_info['has_file_art'] and not album_info['has_flac_art']:
                    self.stats['albums_file_only'] += 1
                elif not album_info['has_file_art'] and album_info['has_flac_art']:
                    self.stats['albums_flac_only'] += 1
                else:
                    self.stats['albums_missing_all'] += 1
                
                # Identify issues
                if not album_info['all_flac_have_art'] and album_info['has_file_art']:
                    self.stats['issues'].append({
                        'type': 'inconsistent_flac',
                        'album': f"{album_info['artist']} / {album_info['album']}",
                        'description': f"Has cover file but some FLAC files missing embedded art"
                    })
                
                if album_info['cover_info'] and 'quality' in album_info['cover_info']:
                    if album_info['cover_info']['quality'] in ['Poor', 'Very Poor']:
                        self.stats['issues'].append({
                            'type': 'low_quality',
                            'album': f"{album_info['artist']} / {album_info['album']}",
                            'description': f"Low quality cover art: {album_info['cover_info']['quality']} ({album_info['cover_info']['dimensions']})"
                        })
        
        return albums
    
    def print_summary(self):
        """Print summary statistics"""
        print("\n📊 Cover Art Analysis Summary")
        print("=" * 50)
        print(f"Total Albums: {self.stats['total_albums']}")
        print(f"Albums with cover files: {self.stats['albums_with_files']} ({self.stats['albums_with_files']/self.stats['total_albums']*100:.1f}%)")
        print(f"Albums with FLAC embedded art: {self.stats['albums_with_flac_art']} ({self.stats['albums_with_flac_art']/self.stats['total_albums']*100:.1f}%)")
        print(f"Albums with both: {self.stats['albums_with_both']} ({self.stats['albums_with_both']/self.stats['total_albums']*100:.1f}%)")
        print(f"Albums missing all cover art: {self.stats['albums_missing_all']}")
        print(f"Albums with file art only: {self.stats['albums_file_only']}")
        print(f"Albums with FLAC art only: {self.stats['albums_flac_only']}")
        
        if self.stats['image_sizes']:
            # Calculate average dimensions
            avg_width = sum(size[0] for size in self.stats['image_sizes']) / len(self.stats['image_sizes'])
            avg_height = sum(size[1] for size in self.stats['image_sizes']) / len(self.stats['image_sizes'])
            print(f"\nAverage cover art size: {avg_width:.0f}x{avg_height:.0f}")
            
            # Show format distribution
            print("\nCover art formats:")
            for format_name, count in sorted(self.stats['file_formats'].items()):
                percentage = count / len(self.stats['image_sizes']) * 100
                print(f"  {format_name}: {count} ({percentage:.1f}%)")
        
        if self.stats['issues']:
            print(f"\n⚠️  Issues Found: {len(self.stats['issues'])}")
            
            # Group issues by type
            issue_types = {}
            for issue in self.stats['issues']:
                issue_type = issue['type']
                if issue_type not in issue_types:
                    issue_types[issue_type] = []
                issue_types[issue_type].append(issue)
            
            for issue_type, issues in issue_types.items():
                print(f"\n{issue_type.replace('_', ' ').title()}: {len(issues)} albums")
                for issue in issues[:5]:  # Show first 5 examples
                    print(f"  • {issue['album']}: {issue['description']}")
                if len(issues) > 5:
                    print(f"  ... and {len(issues) - 5} more")
    
    def print_missing_covers(self, albums: List[Dict]):
        """Print detailed list of albums missing covers"""
        missing = [album for album in albums if not album['has_file_art'] and not album['has_flac_art']]
        
        if not missing:
            print("\n✅ All albums have cover art!")
            return
        
        print(f"\n❌ Albums Missing Cover Art ({len(missing)}):")
        print("=" * 50)
        
        for album in sorted(missing, key=lambda x: (x['artist'], x['album'])):
            print(f"• {album['artist']} / {album['album']}")
            if album['flac_files'] > 0:
                print(f"  📁 {album['flac_files']} FLAC files")
    
    def print_quality_report(self, albums: List[Dict]):
        """Print quality assessment of existing covers"""
        albums_with_covers = [album for album in albums if album['cover_info'] and 'quality' in album['cover_info']]
        
        if not albums_with_covers:
            return
        
        print(f"\n🎨 Cover Art Quality Report ({len(albums_with_covers)} albums):")
        print("=" * 50)
        
        # Group by quality
        quality_groups = {}
        for album in albums_with_covers:
            quality = album['cover_info']['quality']
            if quality not in quality_groups:
                quality_groups[quality] = []
            quality_groups[quality].append(album)
        
        quality_order = ['Excellent', 'Good', 'Fair', 'Poor', 'Very Poor']
        
        for quality in quality_order:
            if quality in quality_groups:
                albums_in_quality = quality_groups[quality]
                print(f"\n{quality}: {len(albums_in_quality)} albums")
                
                if quality in ['Poor', 'Very Poor']:
                    # Show examples of poor quality covers
                    for album in albums_in_quality[:3]:
                        info = album['cover_info']
                        print(f"  • {album['artist']} / {album['album']}")
                        print(f"    {info['dimensions']}, {info['size_kb']}KB")


def main():
    """Main function"""
    if len(sys.argv) != 2:
        print("Usage: python3 cover_art_report.py <output_directory>")
        print("Example: python3 cover_art_report.py output")
        sys.exit(1)
    
    output_dir = Path(sys.argv[1])
    if not output_dir.exists():
        print(f"❌ Output directory does not exist: {output_dir}")
        sys.exit(1)
    
    print("🎨 Cover Art Status Report")
    print("=" * 50)
    
    analyzer = CoverArtAnalyzer()
    albums = analyzer.analyze_collection(output_dir)
    
    # Print reports
    analyzer.print_summary()
    analyzer.print_missing_covers(albums)
    analyzer.print_quality_report(albums)
    
    print(f"\n📝 Analysis complete. Analyzed {len(albums)} albums.")


if __name__ == "__main__":
    main()
