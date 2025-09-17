# Specialized Tools & Utilities

Specialized tools for handling edge cases and specific collection management tasks.

## Tools

### `single_metadata_updater.py` - Singles Metadata Fixer
Fix singles and EPs with generic metadata by applying proper track information.

**Usage:**
```bash
python3 cd_manager.py fix-single "output/Artist/Single Name"
```

**Features:**
- Designed for singles with generic Track_01.flac naming
- Uses Discogs API to find proper track listings
- Updates both filenames and metadata comprehensively
- Handles various single formats (CD singles, maxi-singles, etc.)

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
