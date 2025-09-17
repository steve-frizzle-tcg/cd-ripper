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
├── docs/                  # 📚 Documentation
├── output/                # 🎶 Your organized music collection
├── temp/                  # 📂 Temporary files during ripping
└── logs/                  # 📝 Operation logs
```

## Core Features

### 🎵 CD Ripping & Metadata
- **Error-corrected ripping** using cdparanoia
- **High-quality FLAC** encoding with verification
- **Smart metadata lookup** via MusicBrainz with catalog number priority
- **Multi-disc support** with proper disc-track numbering
- **Various Artists** support for compilations and soundtracks
- **Professional metadata** following industry standards

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

## Command Reference

### Core Operations

#### `rip` - Rip a CD to FLAC
```bash
python3 cd_manager.py rip
```
Interactive CD ripping with metadata lookup and cover art download.

#### `enrich` - Enrich FLAC metadata
```bash
python3 cd_manager.py enrich --apply
python3 cd_manager.py enrich --album "Artist/Album Name"
```
Apply professional metadata standards to existing FLAC files.

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
```
Fix singles with generic metadata using specialized tools.

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

## Advanced Usage

### Working with the Module System

If you need to import functionality into other scripts:

```python
# Add to your Python path
import sys
sys.path.append('/home/steve/cd_ripping/src')

from core.rip_cd import CDRipper
from cover_art.discogs_cover_manager import DiscogsAPI
from reports.cover_art_report import CoverArtAnalyzer
```

### Batch Operations

Process multiple albums efficiently:

```bash
# Process first 20 albums missing covers
python3 cd_manager.py find-missing | head -20 | while read album; do
    python3 cd_manager.py covers "$album"
done

# Enrich metadata for entire collection
python3 cd_manager.py enrich --apply
```

## Troubleshooting

### Common Issues

1. **Permission errors**: Ensure the virtual environment is activated
2. **MusicBrainz timeouts**: The system includes automatic rate limiting
3. **Cover art failures**: Try the manual cover updater for problematic albums
4. **Missing dependencies**: Reinstall with `pip install -r requirements.txt`

### Logs

All operations are logged to `logs/` directory with timestamps for debugging.

### Getting Help

```bash
python3 cd_manager.py --help
python3 cd_manager.py <command> --help
```

## Collection Statistics

Current system manages:
- 316+ albums with 91.5% cover art coverage
- Support for multi-disc sets, compilations, and soundtracks
- Professional metadata with 17+ fields per track
- Automated quality assessment and validation

## Contributing

The modular structure makes it easy to:
- Add new tools to `src/tools/`
- Extend reporting in `src/reports/`
- Enhance cover art sources in `src/cover_art/`
- Improve core functionality in `src/core/`

## Version History

- **v1.0**: Basic CD ripping script
- **v2.0**: Added metadata enrichment and cover art
- **v3.0**: Modular architecture with unified CLI interface
- **Current**: Professional collection management system
