# Project Structure Summary

## 🎯 Main Entry Point
- **`cd_manager.py`** - Unified CLI interface providing access to all functionality

## 📁 Source Code Organization (`src/`)

### 🎵 Core Functionality (`src/core/`)
- **`rip_cd.py`** - Main CD ripping engine with MusicBrainz integration
- **`enrich_metadata.py`** - Professional FLAC metadata enrichment system

### 🎨 Cover Art Management (`src/cover_art/`)
- **`discogs_cover_manager.py`** - Interactive Discogs API-based cover art tool
- **`batch_cover_processor.py`** - Automated batch processing for multiple albums
- **`manual_cover_manager.py`** - Manual cover art addition for special cases
- **`manual_cover_updater.py`** - Replace existing cover art with new images
- **`simple_cover_manager.py`** - Simplified cover art management interface

### 📊 Reports & Analysis (`src/reports/`)
- **`cover_art_report.py`** - Comprehensive collection analysis and quality assessment
- **`find_missing_covers.py`** - Scanner for albums missing cover art

### 🔧 Maintenance & Migration (`src/maintenance/`)
- **`generate_rip_info.py`** - Retroactive rip_info.json generation for existing albums
- **`validate_cover_art.py`** - Cover art validation and integrity checking
- **`migrate_artist.py`** - Artist name migration and reorganization
- **`migrate_compilations.py`** - Compilation album identification and migration
- **`cleanup_empty_dirs.py`** - Directory cleanup and maintenance utilities

### 🛠️ Specialized Tools (`src/tools/`)
- **`single_metadata_updater.py`** - Fix singles with generic metadata
- **`test_artist_choice.py`** - Testing utilities for artist choice functionality

## 📚 Documentation (`docs/`)
- **`core.md`** - Core functionality documentation
- **`cover_art.md`** - Cover art management guide
- **`reports.md`** - Analysis and reporting tools guide

## 🏠 Project Root Files
- **`README.md`** - Main project documentation
- **`METADATA_STANDARDS.md`** - Industry standard metadata reference
- **`migrate_to_new_structure.py`** - Migration helper for transitioning to new structure
- **`.gitignore`** - Git ignore rules

## 📂 Working Directories
- **`output/`** - Organized music collection (Artist/Album structure)
- **`temp/`** - Temporary files during CD ripping process
- **`logs/`** - Operation logs with timestamps
- **`cd_ripping_env/`** - Python virtual environment

## 🎼 Music Collection Structure
```
output/
├── Various Artists/          # Compilation albums
├── Soundtracks/             # Movie/game soundtracks  
├── Artist Name/             # Regular artist albums
│   └── Album Name/
│       ├── 01-01. Track.flac    # Disc-Track numbering
│       ├── cover.jpg            # High-quality artwork
│       └── rip_info.json        # Complete metadata
```

## 🚀 Quick Commands Reference

### Most Common Operations
```bash
python3 cd_manager.py rip              # Rip a new CD
python3 cd_manager.py report           # Collection status
python3 cd_manager.py find-missing     # Find missing covers
python3 cd_manager.py covers           # Interactive cover management
python3 cd_manager.py enrich --apply   # Enhance metadata
```

### Batch Operations
```bash
python3 cd_manager.py batch-covers output --auto --limit 10
python3 cd_manager.py migrate-comps
python3 cd_manager.py cleanup
```

### Specialized Fixes  
```bash
python3 cd_manager.py fix-single "output/Artist/Single"
python3 cd_manager.py replace-cover "output/Artist/Album" new_cover.jpg
python3 cd_manager.py migrate-artist "Old Name" "New Name"
```

## 📈 Benefits of New Structure

1. **Easy Navigation** - Related functionality grouped logically
2. **Scalable** - Easy to add new tools to appropriate categories  
3. **Maintainable** - Clear separation of concerns
4. **User-Friendly** - Single entry point with intuitive commands
5. **Professional** - Industry-standard project organization
6. **Documented** - Comprehensive documentation for each module

## 🔄 Migration from Old Structure

If you have the old flat structure, use the migration helper:
```bash
python3 migrate_to_new_structure.py --backup
```

This preserves all existing functionality while organizing files properly.
