# Maintenance & Migration Tools

Collection maintenance and migration utilities for keeping your music library organized and up-to-date.

## Tools

### `generate_rip_info.py` - Retroactive Metadata Generation
Generate rip_info.json files for existing albums by extracting metadata from FLAC files.

**Usage:**
```bash
python3 cd_manager.py generate-info
```

**Features:**
- Analyzes existing FLAC files to reconstruct album information
- Creates rip_info.json files for albums that don't have them
- Preserves existing metadata while adding missing information
- Batch processing for entire collection

### `validate_cover_art.py` - Cover Art Validation
Validate cover art paths and integrity across your collection.

**Usage:**
```bash
python3 cd_manager.py validate
```

**Features:**
- Checks if cover_art paths in rip_info.json exist
- Automatically corrects paths to actual cover art files
- Identifies albums with broken cover art references
- Batch processing for multiple albums

### `migrate_artist.py` - Artist Migration
Move albums between artist directories for organization and corrections.

**Usage:**
```bash
python3 cd_manager.py migrate-artist "Old Artist Name" "New Artist Name"
```

**Features:**
- Safely moves albums between artist folders
- Updates metadata to reflect new artist names
- Handles conflicts and provides user choice
- Maintains file integrity during moves

### `migrate_compilations.py` - Compilation Migration
Identify and migrate compilation albums to Various Artists folder.

**Usage:**
```bash
python3 cd_manager.py migrate-comps
```

**Features:**
- Identifies likely compilation albums based on naming patterns
- Migrates compilations to Various Artists directory
- Updates album artist metadata appropriately
- Interactive confirmation for each migration

### `cleanup_empty_dirs.py` - Directory Cleanup
Clean up empty directories left after reorganization operations.

**Usage:**
```bash
python3 cd_manager.py cleanup
```

**Features:**
- Scans for empty artist directories
- Safe removal with user confirmation
- Preserves directory structure integrity
- Reports cleanup actions taken

## Common Workflows

### Collection Maintenance
1. Run validation to check integrity: `python3 cd_manager.py validate`
2. Generate missing rip_info files: `python3 cd_manager.py generate-info`
3. Clean up empty directories: `python3 cd_manager.py cleanup`

### Artist Organization
1. Identify compilation albums: `python3 cd_manager.py migrate-comps`
2. Migrate specific artists: `python3 cd_manager.py migrate-artist "Old" "New"`
3. Clean up empty directories: `python3 cd_manager.py cleanup`

### Data Integrity
- All tools include safety checks and user confirmation
- Metadata updates are applied consistently
- File moves preserve audio and metadata integrity
- Comprehensive logging for troubleshooting
