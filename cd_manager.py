#!/usr/bin/env python3
"""
CD Manager - Unified CLI Interface for CD Collection Management

A comprehensive command-line interface that provides access to all CD ripping,
metadata management, cover art management, and collection maintenance tools.

Usage:
    python3 cd_manager.py <command> [options]

Commands:
    Core Operations:
        rip            - Rip a CD to FLAC with metadata
        enrich         - Enrich existing FLAC files with metadata
    
    Cover Art Management:
        covers         - Interactive cover art management
        batch-covers   - Batch process cover art for multiple albums
        find-missing   - Find albums missing cover art
        replace-cover  - Replace cover art for specific album
    
    Collection Analysis:
        report         - Generate comprehensive collection report
        validate       - Validate cover art and metadata integrity
    
    Maintenance & Migration:
        generate-info  - Generate rip_info.json for existing albums
        migrate-artist - Migrate albums between artists
        migrate-comps  - Identify and migrate compilation albums
        cleanup        - Clean up empty directories
    
    Specialized Tools:
        fix-single     - Fix metadata for singles with generic names
        test-choice    - Test artist choice functionality

Examples:
    python3 cd_manager.py rip
    python3 cd_manager.py covers
    python3 cd_manager.py report --detailed
    python3 cd_manager.py batch-covers --auto --limit 10
    python3 cd_manager.py migrate-artist "Old Name" "New Name"
"""

import sys
import argparse
import subprocess
from pathlib import Path

# Add src directory to Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

def run_script(script_path, args=None):
    """Run a script with optional arguments"""
    cmd = [sys.executable, str(script_path)]
    if args:
        cmd.extend(args)
    
    try:
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error running {script_path.name}: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\nOperation cancelled by user")
        sys.exit(0)

def main():
    parser = argparse.ArgumentParser(
        description="CD Manager - Unified CD Collection Management",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__.split('Examples:')[1] if 'Examples:' in __doc__ else ""
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Core Operations
    core_parser = subparsers.add_parser('rip', help='Rip a CD to FLAC')
    
    enrich_parser = subparsers.add_parser('enrich', help='Enrich FLAC metadata')
    enrich_parser.add_argument('--apply', action='store_true', help='Apply changes')
    enrich_parser.add_argument('--album', help='Target specific album')
    
    # Cover Art Management
    covers_parser = subparsers.add_parser('covers', help='Interactive cover art management')
    
    batch_parser = subparsers.add_parser('batch-covers', help='Batch cover art processing')
    batch_parser.add_argument('path', help='Path to process')
    batch_parser.add_argument('--auto', action='store_true', help='Automatic processing')
    batch_parser.add_argument('--limit', type=int, help='Limit number of albums')
    
    find_parser = subparsers.add_parser('find-missing', help='Find missing cover art')
    find_parser.add_argument('--interactive', action='store_true', help='Interactive mode with cover search')
    
    replace_parser = subparsers.add_parser('replace-cover', help='Replace cover art')
    replace_parser.add_argument('album_path', help='Path to album directory')
    replace_parser.add_argument('image_file', help='New cover image file')
    
    # Collection Analysis
    report_parser = subparsers.add_parser('report', help='Collection analysis report')
    report_parser.add_argument('--directory', default='output', help='Output directory to analyze (default: output)')
    
    validate_parser = subparsers.add_parser('validate', help='Validate collection integrity')
    
    # Maintenance & Migration
    generate_parser = subparsers.add_parser('generate-info', help='Generate rip_info.json files')
    
    migrate_artist_parser = subparsers.add_parser('migrate-artist', help='Migrate artist')
    migrate_artist_parser.add_argument('old_name', help='Old artist name')
    migrate_artist_parser.add_argument('new_name', help='New artist name')
    
    migrate_comps_parser = subparsers.add_parser('migrate-comps', help='Migrate compilations')
    
    cleanup_parser = subparsers.add_parser('cleanup', help='Clean up empty directories')
    
    # Specialized Tools
    fix_single_parser = subparsers.add_parser('fix-single', help='Fix single metadata')
    fix_single_parser.add_argument('album_path', help='Path to single album')
    
    test_parser = subparsers.add_parser('test-choice', help='Test artist choice')
    
    # Date analyzer tool
    date_parser = subparsers.add_parser('analyze-dates', help='Analyze and fix date metadata consistency')
    date_parser.add_argument('output_dir', nargs='?', default='output', help='Output directory to analyze')
    date_parser.add_argument('--apply', action='store_true', help='Apply fixes (default is dry run)')
    date_parser.add_argument('--export', help='Export analysis to JSON file')
    date_parser.add_argument('--show-all', action='store_true', help='Show all albums, not just problematic ones')
    
    # Multi-disc fixer tool
    multifix_parser = subparsers.add_parser('fix-multidisc', help='Fix multi-disc album metadata (DISCNUMBER, TRACKNUMBER)')
    multifix_parser.add_argument('album_path', help='Path to multi-disc album directory')
    multifix_parser.add_argument('--apply', action='store_true', help='Apply fixes (default is dry run)')
    
    # Track number normalizer tool
    tracknorm_parser = subparsers.add_parser('normalize-tracks', help='Normalize track numbers to Vorbis standards (collection-wide)')
    tracknorm_parser.add_argument('path', nargs='?', default='output', help='Path to collection or album directory')
    tracknorm_parser.add_argument('--apply', action='store_true', help='Apply fixes (default is dry run)')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    # Map commands to script paths
    script_root = Path(__file__).parent
    
    command_map = {
        # Core Operations
        'rip': script_root / 'src' / 'core' / 'rip_cd.py',
        'enrich': script_root / 'src' / 'core' / 'enrich_metadata.py',
        
        # Cover Art Management
        'covers': script_root / 'src' / 'cover_art' / 'discogs_cover_manager.py',
        'batch-covers': script_root / 'src' / 'cover_art' / 'batch_cover_processor.py',
        'find-missing': script_root / 'src' / 'reports' / 'find_missing_covers.py',
        'replace-cover': script_root / 'src' / 'cover_art' / 'manual_cover_updater.py',
        
        # Collection Analysis
        'report': script_root / 'src' / 'reports' / 'cover_art_report.py',
        'validate': script_root / 'src' / 'maintenance' / 'validate_cover_art.py',
        
        # Maintenance & Migration
        'generate-info': script_root / 'src' / 'maintenance' / 'generate_rip_info.py',
        'migrate-artist': script_root / 'src' / 'maintenance' / 'migrate_artist.py',
        'migrate-comps': script_root / 'src' / 'maintenance' / 'migrate_compilations.py',
        'cleanup': script_root / 'src' / 'maintenance' / 'cleanup_empty_dirs.py',
        
        # Specialized Tools
        'fix-single': script_root / 'src' / 'tools' / 'single_metadata_updater.py',
        'test-choice': script_root / 'src' / 'tools' / 'test_artist_choice.py',
        'analyze-dates': script_root / 'src' / 'tools' / 'date_analyzer.py',
        'fix-multidisc': script_root / 'src' / 'tools' / 'multi_disc_fixer.py',
        'normalize-tracks': script_root / 'src' / 'tools' / 'track_normalizer.py',
    }
    
    if args.command not in command_map:
        print(f"Unknown command: {args.command}")
        parser.print_help()
        return
    
    script_path = command_map[args.command]
    
    # Build arguments for the target script
    script_args = []
    
    if args.command == 'enrich':
        if args.apply:
            script_args.append('--apply')
        if args.album:
            script_args.extend(['--album', args.album])
    
    elif args.command == 'batch-covers':
        script_args.append(args.path)
        if args.auto:
            script_args.append('--auto')
        if args.limit:
            script_args.extend(['--limit', str(args.limit)])
    
    elif args.command == 'report':
        script_args.append(args.directory)
    
    elif args.command == 'migrate-artist':
        script_args.extend([args.old_name, args.new_name])
    
    elif args.command == 'find-missing':
        if not args.interactive:
            script_args.append('--simple')
    
    elif args.command == 'replace-cover':
        script_args.extend([args.album_path, args.image_file])
    
    elif args.command == 'fix-single':
        script_args.append(args.album_path)
    
    elif args.command == 'analyze-dates':
        script_args.append(args.output_dir)
        if args.apply:
            script_args.append('--apply')
        if args.export:
            script_args.extend(['--export', args.export])
        if args.show_all:
            script_args.append('--show-all')
    
    elif args.command == 'fix-multidisc':
        script_args.append(args.album_path)
        if args.apply:
            script_args.append('--apply')
    
    elif args.command == 'normalize-tracks':
        script_args.append(args.path)
        if args.apply:
            script_args.append('--apply')
    
    # Run the target script
    print(f"🎵 Running: {script_path.name}")
    print("=" * 60)
    run_script(script_path, script_args)

if __name__ == "__main__":
    main()
