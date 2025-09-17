#!/usr/bin/env python3
"""
Batch Cover Art Processor
Simplified interface for processing multiple albums missing cover art.
"""

import sys
from pathlib import Path
from discogs_cover_manager import DiscogsCoverManager

def main():
    """Main function for batch processing"""
    if len(sys.argv) < 2:
        print("Usage: python3 batch_cover_processor.py <output_directory> [--auto] [--limit N]")
        print("Example: python3 batch_cover_processor.py output --auto --limit 5")
        print("\nOptions:")
        print("  --auto     Auto-select best match without user input")
        print("  --limit N  Process only N albums (useful for testing)")
        sys.exit(1)
    
    output_dir = Path(sys.argv[1])
    if not output_dir.exists():
        print(f"❌ Output directory does not exist: {output_dir}")
        sys.exit(1)
    
    auto_mode = '--auto' in sys.argv
    limit = None
    
    # Parse limit argument
    if '--limit' in sys.argv:
        try:
            limit_idx = sys.argv.index('--limit') + 1
            if limit_idx < len(sys.argv):
                limit = int(sys.argv[limit_idx])
        except (ValueError, IndexError):
            print("❌ Invalid limit value")
            sys.exit(1)
    
    print("🎨 Batch Cover Art Processor")
    print("=" * 50)
    
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
    
    # Apply limit if specified
    if limit and limit < len(missing_covers):
        missing_covers = missing_covers[:limit]
        print(f"📋 Processing first {limit} albums (--limit {limit} specified)")
    
    print(f"\n📋 Found {len(missing_covers)} albums to process:")
    for i, album_dir in enumerate(missing_covers):
        artist = album_dir.parent.name
        album = album_dir.name
        print(f"   {i+1:2d}. {artist} / {album}")
    
    if not auto_mode:
        proceed = input(f"\nProcess these {len(missing_covers)} albums? (y/n): ").lower().strip()
        if proceed != 'y':
            print("👋 Cancelled by user")
            return
    
    print(f"\n🎵 Processing albums in {'automatic' if auto_mode else 'interactive'} mode...")
    print("=" * 80)
    
    successful = 0
    skipped = 0
    
    for i, album_dir in enumerate(missing_covers):
        artist = album_dir.parent.name
        album = album_dir.name
        
        print(f"\n📁 [{i+1}/{len(missing_covers)}] {artist} / {album}")
        
        try:
            if auto_mode:
                # Auto mode: select best match automatically
                result = process_album_auto(manager, album_dir)
            else:
                # Interactive mode: let user choose
                result = manager.process_album(album_dir)
            
            if result:
                successful += 1
                print("✅ Success!")
            else:
                skipped += 1
                print("⏭️  Skipped")
            
        except KeyboardInterrupt:
            print("\n⏹️  Process interrupted by user")
            break
        except Exception as e:
            print(f"❌ Error: {e}")
            skipped += 1
    
    print(f"\n📊 Batch Processing Complete!")
    print(f"   Processed: {successful + skipped}/{len(missing_covers)}")
    print(f"   Successful: {successful}")
    print(f"   Skipped: {skipped}")


def process_album_auto(manager: DiscogsCoverManager, album_dir: Path) -> bool:
    """Process album automatically without user input"""
    artist = album_dir.parent.name
    album = album_dir.name
    
    # Search for releases
    results = manager.api.search_releases(artist, album)
    
    if not results:
        print("❌ No search results")
        return False
    
    # Auto-select best match (first result with high confidence)
    best_result = None
    for result in results[:3]:  # Check top 3 results
        title = result.get('title', '').lower()
        if (artist.lower() in title and album.lower() in title):
            best_result = result
            break
    
    if not best_result:
        best_result = results[0]  # Fallback to first result
    
    release_id = str(best_result['id'])
    print(f"🎯 Auto-selected: {best_result.get('title', 'Unknown')}")
    
    # Get release details
    release_details = manager.api.get_release_details(release_id)
    if not release_details:
        print("❌ Failed to get release details")
        return False
    
    # Get images
    images = release_details.get('images', [])
    if not images:
        print("❌ No images found")
        return False
    
    # Filter for primary/cover images
    cover_images = [img for img in images if img.get('type') == 'primary']
    if not cover_images:
        cover_images = images
    
    selected_image = cover_images[0]
    image_url = selected_image.get('uri')
    
    if not image_url:
        print("❌ No image URL")
        return False
    
    # Download image
    cover_path = manager.download_cover_image(image_url, album_dir, release_details)
    
    if not cover_path:
        print("❌ Download failed")
        return False
    
    # Add to FLAC files
    manager.add_cover_to_flac_files(album_dir, cover_path)
    
    # Update rip_info.json
    rip_info_path = album_dir / 'rip_info.json'
    if rip_info_path.exists():
        try:
            import json
            with open(rip_info_path, 'r') as f:
                rip_info = json.load(f)
            
            rip_info['cover_art'] = cover_path.name
            rip_info['discogs_release_id'] = release_id
            
            with open(rip_info_path, 'w') as f:
                json.dump(rip_info, f, indent=2)
                
        except Exception as e:
            print(f"⚠️  Could not update rip_info.json: {e}")
    
    return True


if __name__ == "__main__":
    main()
