# Core Functionality Documentation

## rip_cd.py - CD Ripping Engine

The main CD ripping script that handles the complete process from physical CD to organized FLAC files.

### Features
- cdparanoia integration for error-corrected ripping
- MusicBrainz metadata lookup with catalog number priority  
- Multi-disc support with proper numbering
- Various Artists detection for compilations
- Automatic cover art download
- Comprehensive logging

### Usage
```bash
python3 cd_manager.py rip
```

### Process Flow
1. Detect CD and extract track information
2. Rip audio tracks to temporary WAV files
3. Look up metadata via MusicBrainz (catalog number first)
4. User confirmation/editing of metadata
5. Convert to FLAC with metadata
6. Download cover art
7. Organize into proper directory structure
8. Generate rip_info.json

## rip_individual_track.py - Individual Track Recovery System

Complete partially ripped albums by adding missing tracks without affecting existing ones.

### Features
- Smart detection of missing tracks from any album
- Interactive album selection from incomplete albums
- Enhanced error recovery for problematic tracks
- Automatic metadata integration with existing collection
- Preserves existing tracks and organization
- Multiple recovery methods (standard, aggressive error correction, force through errors)

### Usage
```bash
# Interactive mode - select from incomplete albums
python3 cd_manager.py rip-track

# Direct mode - specify album path
python3 cd_manager.py rip-track "/path/to/album"

# List incomplete albums
python3 cd_manager.py rip-track --list-incomplete

# List all albums with completion status
python3 cd_manager.py rip-track --list-all
```

### Recovery Methods
1. **Standard Rip**: Normal cdparanoia extraction
2. **Enhanced Recovery**: Reduced overlap with maximum retries (`-o 1 -Y`)
3. **Force Through Errors**: Skip verification and force output (`-Z`, `-X`)
4. **Extended Timeout**: Up to 10 minutes for difficult tracks

### Use Cases
- Complete albums where individual tracks failed during original rip
- Re-rip damaged or corrupted tracks
- Add tracks that were skipped due to errors
- Recovery from CD reading issues or timeouts

## enrich_metadata.py - Metadata Enrichment System

Professional metadata enrichment system that applies industry standards to FLAC files.

### Features
- 5-level metadata standard (Required, Standard, MusicBrainz, Extended, Technical)
- Batch processing for entire collection
- MusicBrainz integration for enhanced data
- Consistency validation across albums
- ReplayGain calculation

### Usage
```bash
# Interactive mode - preview changes
python3 cd_manager.py enrich

# Apply changes automatically
python3 cd_manager.py enrich --apply

# Target specific album
python3 cd_manager.py enrich --album "Artist/Album Name"
```

### Metadata Standards

#### Required Fields
- ALBUM, ALBUMARTIST, ARTIST, TITLE, TRACKNUMBER, DISCNUMBER, DATE

#### Standard Fields  
- GENRE, LABEL, CATALOGNUMBER, TOTALTRACKS, TOTALDISCS

#### MusicBrainz Fields
- MUSICBRAINZ_ALBUMID, MUSICBRAINZ_ARTISTID, MUSICBRAINZ_TRACKID
- RELEASECOUNTRY, BARCODE

#### Extended Fields
- COMPOSER, PRODUCER, ENGINEER, MATRIXNUMBER

#### Technical Fields
- ENCODER, ENCODERSETTINGS, REPLAYGAIN_*
