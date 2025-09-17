# CD Manager - Professional CD Collection Management System

## Overview

A comprehensive, well-organized system for ripping CDs to high-quality FLAC files with professional metadata enrichment, cover art management, and collection maintenance tools. The system has evolved from a single script into a modular, easy-to-use suite of tools accessible through a unified command-line interface.

## Quick Start

```bash
# Rip a new CD
python3 cd_manager.py rip

# Check collection status  
python3 cd_manager.py report

# Find albums missing cover art
python3 cd_manager.py find-missing

# Interactive cover art management
python3 cd_manager.py covers

# Enrich metadata for existing albums
python3 cd_manager.py enrich --apply
```

## Core Features

### 🎵 CD Ripping & Metadata
- **Error-corrected ripping** using cdparanoia
- **High-quality FLAC** encoding with verification
- **Smart metadata lookup** via MusicBrainz with catalog number priority
- **Multi-disc support** with proper disc-track numbering (01-01 format)
- **Various Artists** support for compilations and soundtracks
- **Professional metadata** following industry standards (17+ fields)

### 🎨 Cover Art Management  
- **Discogs integration** for high-quality cover art
- **Batch processing** for multiple albums
- **Quality assessment** and validation
- **Manual replacement** tools
- **Automatic embedding** in FLAC files

### 📊 Collection Analysis
- **Comprehensive reporting** on collection status
- **Cover art quality assessment**
- **Missing content identification**
- **Integrity validation**

### 🔧 Maintenance Tools
- **Retroactive metadata** generation for existing albums
- **Artist migration** and reorganization  
- **Compilation identification** and organization
- **Directory cleanup** utilities

## Installation & Setup

### Prerequisites

```bash
# Ubuntu/Debian system requirements
sudo apt update
sudo apt install -y cdparanoia flac python3 python3-pip python3-venv eject

# Create and activate virtual environment
python3 -m venv ~/cd_ripping/cd_ripping_env
source ~/cd_ripping/cd_ripping_env/bin/activate

# Install Python dependencies
pip install musicbrainzngs requests mutagen pillow
```

### Configuration

1. **MusicBrainz**: No additional setup required
2. **Discogs API** (optional, for enhanced cover art):
   ```bash
   # Create ~/.config/discogs/config.ini
   [discogs]
   user_token = your_discogs_user_token_here
   ```

## System Architecture

The project is organized into logical modules for easy maintenance and understanding:

```
cd_ripping/
├── cd_manager.py           # 🎯 Main entry point - unified CLI interface
├── src/                    # 📁 Source code organized by functionality
│   ├── core/              # 🎵 Core ripping and metadata functionality
│   ├── cover_art/         # 🎨 Cover art management tools
│   ├── reports/           # 📊 Analysis and reporting tools
│   ├── maintenance/       # 🔧 Collection maintenance utilities
│   └── tools/             # 🛠️ Specialized tools and utilities
├── output/                # 🎶 Your organized music collection
├── temp/                  # 📂 Temporary files during ripping
└── logs/                  # 📝 Operation logs
```

## Command Reference

### Core Operations

#### `rip` - Rip a CD to FLAC
```bash
python3 cd_manager.py rip
```
Interactive CD ripping with metadata lookup and cover art download.

**Process Flow:**
1. Insert CD and detect tracks
2. Select album type (Regular, Soundtrack, Compilation)
3. Enter catalog number (optional but recommended)
4. Enter basic artist/album information
5. Automatic track ripping (5-10 minutes)
6. MusicBrainz metadata lookup
7. Cover art download
8. File organization and metadata embedding

#### `enrich` - Enrich FLAC metadata
```bash
python3 cd_manager.py enrich --apply
python3 cd_manager.py enrich --album "Artist/Album Name"
```
Apply professional metadata standards to existing FLAC files (17+ fields).

### Cover Art Management

#### `covers` - Interactive cover art management
```bash
python3 cd_manager.py covers
```
Interactive Discogs-powered cover art management with search and preview.

#### `batch-covers` - Batch cover art processing
```bash
python3 cd_manager.py batch-covers output --auto --limit 10
```
Automated batch processing for multiple albums.

#### `find-missing` - Find missing cover art
```bash
python3 cd_manager.py find-missing
python3 cd_manager.py find-missing --interactive
```
Scan collection for albums without cover art.

#### `replace-cover` - Replace cover art
```bash
python3 cd_manager.py replace-cover "output/Artist/Album" new_cover.jpg
```
Replace existing cover art with a new image.

### Collection Analysis

#### `report` - Collection analysis report
```bash
python3 cd_manager.py report
python3 cd_manager.py report --directory /path/to/music
```
Comprehensive analysis of collection status, cover art quality, and statistics.

#### `validate` - Validate collection integrity
```bash
python3 cd_manager.py validate
```
Check cover art paths and metadata integrity.

### Maintenance & Migration

#### `generate-info` - Generate rip_info.json files
```bash
python3 cd_manager.py generate-info
```
Create rip_info.json files for existing albums by extracting FLAC metadata.

#### `migrate-artist` - Migrate artist
```bash
python3 cd_manager.py migrate-artist "Old Artist Name" "New Artist Name"
```
Move albums between artist directories.

#### `migrate-comps` - Migrate compilations
```bash
python3 cd_manager.py migrate-comps
```
Identify and migrate compilation albums to Various Artists.

#### `cleanup` - Clean up empty directories
```bash
python3 cd_manager.py cleanup
```
Remove empty artist directories after reorganization.

### Specialized Tools

#### `fix-single` - Fix single metadata
```bash
python3 cd_manager.py fix-single "output/Artist/Single Name"
## File Organization

The system creates a clean, organized structure:

```
output/
├── Various Artists/           # Compilation albums
│   ├── Album Name/
│   │   ├── 01-01. Track.flac
│   │   ├── cover.jpg
│   │   └── rip_info.json
├── Artist Name/               # Regular albums
│   ├── Album Name/
│   │   ├── 01-01. Track.flac  # Disc-Track format
│   │   ├── 01-02. Track.flac
│   │   ├── cover.jpg          # High-quality cover art
│   │   └── rip_info.json      # Complete album metadata
└── Soundtracks/               # Movie/game soundtracks
    └── Movie Name/
        ├── 01-01. Track.flac
        ├── cover.jpg
        └── rip_info.json
```

## Metadata Standards

The system follows a comprehensive 5-level metadata standard:

### Required Fields (Always Present)
- Album, Album Artist, Artist, Title, Track Number, Disc Number, Date

### Standard Fields (Recommended)
- Genre, Label, Catalog Number, Total Tracks, Total Discs

### MusicBrainz Fields (Enhanced)
- MusicBrainz IDs, Release Country, Barcode

### Extended Fields (Professional)
- Composer, Producer, Engineer, Matrix Numbers

### Technical Fields (Quality)
- Encoder, Encoding Settings, ReplayGain

## Advanced Features

### Album Type Support

#### Regular Albums (Single Artist)
- Standard single-artist releases
- Artist name applies to all tracks
- Standard MusicBrainz lookup by artist and album

#### Soundtracks (Various Artists)
- Movie, TV show, or game soundtracks
- Organized in `output/Soundtracks/Album Name/` directory
- Individual track artists from MusicBrainz or manual entry
- Enhanced filename format: `01-01. Artist - Track Title.flac`

#### Compilations (Various Artists)
- "Now That's What I Call Music" style releases
- Multiple artists across different tracks
- Same handling as soundtracks with Various Artists support

### Catalog Number Support

Unique identifiers printed on CDs for precise metadata lookup:
- **Examples**: `GEFD-24617`, `CDV 2644`, `7599-26985-2`
- **Benefits**: Most precise metadata lookup method available
- **Enhanced Input**: Flexible format handling with auto-normalization
- **Multiple Search**: Tries various format combinations automatically

### Multi-Disc Album Support
- **File naming**: Uses `Disc-Track` format (e.g., `01-01`, `02-03`)
- **Single discs**: Automatically use `01-XX` format for consistency
- **Multi-disc sets**: Specify disc number during initial setup
- **Metadata**: Includes proper disc number and total disc count

## Troubleshooting

### Getting Help
```bash
python3 cd_manager.py --help
python3 cd_manager.py <command> --help
```

### Common Issues
1. **Permission errors**: Ensure the virtual environment is activated
2. **MusicBrainz timeouts**: The system includes automatic rate limiting
3. **Cover art failures**: Try the manual cover updater for problematic albums
4. **Missing dependencies**: Reinstall with `pip install -r requirements.txt`

### Logs
All operations are logged to `logs/` directory with timestamps for debugging.
- **Safe Operation**: Only removes directories confirmed to be completely empty
- **Detailed Logging**: Shows what files were moved and which directories were cleaned up

#### **Manual Cleanup Tool**
Run `python3 cleanup_empty_dirs.py` to:
- Scan for empty artist directories
- Show which directories contain albums vs. empty ones
- Safely remove empty directories with confirmation
- Perfect for cleaning up after reorganizations

### Common Issues
- **No CD detected**: Check CD drive connection and permissions
- **MusicBrainz failures**: Script continues with manual metadata entry
- **Track ripping errors**: Individual track failures don't stop the process
- **Permission errors**: Ensure user has access to CD drive (`/dev/cdrom`)
- **Dialogue tracks**: Movie soundtracks may include dialogue/scene audio with problematic metadata - automatically cleaned to "Unknown Artist"
- **Invalid artist names**: Malformed MusicBrainz data (like " & ") is automatically cleaned or replaced with "Unknown Artist"
- **Catalog number format**: Invalid catalog numbers are rejected with format guidance - enter 3-20 alphanumeric characters
- **Catalog number not found**: System falls back to artist/album search automatically
- **Multiple catalog matches**: User prompted to select correct release from list
- **Foreign language names**: System prompts to choose between your input and MusicBrainz version when significantly different
- **Empty directories**: Automatically cleaned up during reorganization; use cleanup script for manual cleanup

### Log Files
Check `logs/rip_cd_YYYYMMDD_HHMMSS.log` for detailed error information.

## Cover Art Management

The system includes comprehensive cover art management tools for finding, validating, and applying album artwork to your collection.

### Cover Art Analysis
```bash
# Get comprehensive cover art status report
python3 cover_art_report.py output
```

**Provides detailed analysis:**
- **Coverage Statistics**: Shows percentage of albums with cover art
- **Quality Assessment**: Evaluates cover art resolution and file size
- **Issue Detection**: Identifies albums with low-quality or missing covers
- **Format Distribution**: Reports JPEG vs PNG usage across collection
- **Missing Albums List**: Detailed list of albums needing cover art

### Finding Missing Covers
```bash
# Find albums missing cover art files
python3 find_missing_covers.py output
```

**Scans for albums missing:**
- Cover art files (`cover.jpg`, `folder.jpg`, etc.)
- Embedded FLAC artwork
- Shows FLAC file counts per album

### Discogs Cover Art Manager

**Interactive cover art search and download using the Discogs API:**

```bash
# Interactive mode - choose each album manually  
python3 discogs_cover_manager.py output

# Batch processing with automatic selection
python3 batch_cover_processor.py output --auto

# Process only first 5 albums (testing)
python3 batch_cover_processor.py output --auto --limit 5
```

#### **Discogs API Setup**
1. **Create Account**: Visit https://www.discogs.com and create free account
2. **Generate Token**: Go to https://www.discogs.com/settings/developers
3. **Create Token**: Click "Generate new token", name it "CD Ripper Cover Art"
4. **Copy Token**: Script will prompt for token on first run
5. **Automatic Storage**: Token saved securely for future use

#### **Features**
- **Smart Search**: Multiple search strategies with artist/album matching
- **Quality Scoring**: Ranks results by relevance and confidence
- **Multiple Sources**: Discogs primary, with MusicBrainz and manual fallbacks
- **Rate Limiting**: Respects API limits with automatic throttling
- **Image Processing**: Automatic resizing and format optimization
- **FLAC Integration**: Embeds cover art directly into FLAC files
- **Metadata Updates**: Updates `rip_info.json` with cover art information

#### **Interactive Mode Process**
1. **Authentication**: Automatic token verification and setup
2. **Scan Collection**: Finds all albums missing cover art
3. **Search Results**: Shows ranked Discogs releases with metadata
4. **User Selection**: Choose correct release from search results
5. **Image Download**: Downloads and processes cover art
6. **FLAC Embedding**: Adds artwork to all FLAC files in album
7. **Metadata Update**: Updates rip_info.json with cover details

#### **Automatic Mode**
- **Best Match Selection**: Automatically selects highest-confidence match
- **Batch Processing**: Processes multiple albums without user intervention
- **Fallback Handling**: Skips problematic albums and continues
- **Progress Tracking**: Shows processing status and success rates

#### **Fallback Options**
When Discogs images are blocked or unavailable:
1. **Manual Discogs Download**: Guided browser-based download
2. **MusicBrainz Cover Art Archive**: Alternative automatic source
3. **Google Images Search**: Guided manual search and download
4. **Skip Option**: Continue to next album

## Collection Statistics

Current system manages:
- **316+ albums** with 91.5% cover art coverage
- **Support** for multi-disc sets, compilations, and soundtracks
- **Professional metadata** with 17+ fields per track
- **Automated quality assessment** and validation

## Version History

- **v1.0**: Basic CD ripping script
- **v2.0**: Added metadata enrichment and cover art
- **v3.0**: Modular architecture with unified CLI interface
- **Current**: Professional collection management system