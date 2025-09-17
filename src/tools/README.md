# Specialized Tools & Utilities

Specialized tools for handling edge cases and specific collection management tasks.

## Available Tools

### `date_analyzer.py` - Date metadata analysis and standardization
```bash
python3 cd_manager.py analyze-dates                    # Analyze collection
python3 cd_manager.py analyze-dates --apply            # Fix date issues
python3 cd_manager.py analyze-dates --export dates.json # Export analysis
```
Comprehensive date metadata analysis and correction tool that ensures FLAC Vorbis comment compliance.

### `multi_disc_fixer.py` - Multi-disc album metadata correction
```bash
python3 cd_manager.py fix-multidisc "output/Artist/Album"        # Analyze issues
python3 cd_manager.py fix-multidisc "output/Artist/Album" --apply # Apply fixes
```
Fixes DISCNUMBER and TRACKNUMBER metadata for multi-disc albums with X-YY filename patterns.

### `single_metadata_updater.py` - Single track metadata editor
```bash
python3 cd_manager.py fix-single "output/Artist/Single Name"
```
Fix singles with generic metadata using specialized tools.

**Example Case:** Annie Lennox Walking On Broken Glass single
- Before: Track_01.flac, Track_02.flac (generic names)
- After: 01-01. Walking On Broken Glass (Single Version).flac, 01-02. River Deep, Mountain High.flac

### `test_artist_choice.py` - Testing Utilities
Testing utilities for artist choice functionality and system validation.

**Usage:**
```bash
python3 cd_manager.py test-choice
```

**Features:**
- Tests artist name handling and selection logic
- Validates metadata processing workflows
- Debugging tools for development and troubleshooting
- Quality assurance for system functionality

## Use Cases

### When to Use Singles Fixer
- CDs ripped with generic track names
- Singles lacking proper metadata
- EPs with insufficient track information
- Promotional releases with limited data

### When to Use Testing Tools
- System debugging and validation
- Development of new features
- Quality assurance testing
- Troubleshooting metadata issues

## Integration

These tools integrate with the main cd_manager.py interface but are designed for specific, less common scenarios. They provide solutions for edge cases that don't fit the standard workflow but are essential for maintaining a complete, professional collection.
