# CD Ripper - Automated Music CD Ripping to FLAC

## Overview
A comprehensive Python script for ripping music CDs to high-quality FLAC files with automatic metadata enrichment via MusicBrainz. The process prioritizes reliability by separating the ripping and metadata phases, ensuring you get FLAC files even if metadata lookup fails.

## Features

- **Reliable CD Ripping**: Uses `cdparanoia` for error-corrected audio extraction
- **High-Quality Output**: FLAC compression with verification
- **Smart Metadata**: MusicBrainz integration with track count validation
- **Organized Structure**: Creates nested `Artist/Album` directories with proper naming
- **Cover Art**: Automatic download from Cover Art Archive
- **Error Resilience**: Continues ripping even if individual tracks or metadata fail
- **Comprehensive Logging**: Detailed logs for troubleshooting

## Prerequisites

### System Requirements
- Ubuntu/Debian Linux system
- CD/DVD drive
- Python 3.7+
- Internet connection (for metadata lookup)

### Required Packages
```bash
# Install required system packages
sudo apt update
sudo apt install -y \
    cdparanoia \
    flac \
    python3 \
    python3-pip \
    python3-venv \
    eject

# Create and activate virtual environment
python3 -m venv ~/cd_ripping/cd_ripping_env
source ~/cd_ripping/cd_ripping_env/bin/activate

# Install Python dependencies
pip install musicbrainzngs requests mutagen
```

### Directory Structure
The script automatically creates this structure:
```
~/cd_ripping/
├── rip_cd.py           # Main ripping script
├── temp/               # Temporary WAV files during ripping
├── output/             # Final organized FLAC files
│   ├── Artist Name/
│   │   └── Album Name/
│   │       ├── 01-01. Track Name.flac
│   │       ├── 01-02. Track Name.flac
│   │       ├── cover.jpg
│   │       └── rip_info.json
├── logs/               # Ripping session logs
└── cd_ripping_env/     # Python virtual environment
```

## How It Works

### 1. **Initial Setup**
- Prompts for basic artist and album information
- Detects CD drive and counts tracks
- Creates working directories

### 2. **Track Ripping Phase**
- Rips each track individually using `cdparanoia`
- Converts WAV to FLAC with maximum compression
- Creates temporary files with generic names (`Track_01.flac`, etc.)
- Continues even if individual tracks fail

### 3. **Metadata Enhancement Phase**
- Searches MusicBrainz for album information
- Validates matches against actual track count
- Downloads proper track titles and artist information
- Falls back to manual entry if MusicBrainz fails

### 4. **Organization Phase**
- Reorganizes files into proper `Artist/Album` directory structure
- Renames files with actual track titles (e.g., `01. Track Name.flac`)
- Adds comprehensive metadata to FLAC files
- Downloads album cover art when available

### 5. **Final Output**
- Creates `rip_info.json` with ripping session details
- Logs all activity for troubleshooting
- Ejects CD automatically when complete

## Usage

### Basic Usage
```bash
# Activate virtual environment
source ~/cd_ripping/cd_ripping_env/bin/activate

# Navigate to project directory
cd ~/cd_ripping

# Insert CD and run the script
python3 rip_cd.py
```

### Interactive Process
1. **Insert CD** and press Enter to start
2. **Select album type**: Regular Album, Soundtrack, or Compilation
3. **Enter catalog number** (optional): Provides most accurate metadata lookup
4. **Enter basic info**: Artist/album details based on type, year (optional), disc number (for multi-disc albums)
5. **Automatic ripping**: Script rips all tracks (5-10 minutes typical)
6. **Metadata enhancement**: Automatic MusicBrainz lookup with catalog number priority
7. **Completion**: Files organized in appropriate directory structure

### Album Type Support

#### **Regular Albums (Single Artist)**
- Standard single-artist releases
- Artist name applies to all tracks
- Standard MusicBrainz lookup by artist and album

#### **Soundtracks (Various Artists)**
- Movie, TV show, or game soundtracks
- Organized in `output/Soundtracks/Album Name/` directory structure
- Individual track artists from MusicBrainz or manual entry
- Enhanced filename format: `01-01. Artist - Track Title.flac`
- Automatic cleanup of problematic artist names (e.g., dialogue tracks)

#### **Compilations (Various Artists)**
- "Now That's What I Call Music" style releases
- Multiple artists across different tracks
- Same handling as soundtracks with Various Artists support

### Catalog Number Support

#### **What are Catalog Numbers?**
Unique identifiers printed on CDs, usually on the spine, back cover, or disc itself:
- **Examples**: `GEFD-24617`, `CDV 2644`, `7599-26985-2`, `B0001234-02`
- **Benefits**: Most precise metadata lookup method available
- **Location**: Check CD spine, back cover, or printed on the disc

#### **Enhanced Input Handling**
- **Flexible Format**: Accepts various formats with/without spaces and hyphens
- **Auto-Normalization**: Automatically standardizes format (removes spaces, etc.)
- **Validation**: Checks format and prompts for confirmation
- **Multiple Attempts**: Up to 3 attempts with helpful error messages
- **User Confirmation**: Shows normalized version before proceeding

#### **Examples of Input Variations**
```
User Input          →  Search Priority        →  Also Searches
"ACD 8754"          →  1. "ACD 8754"         →  "ACD8754", "ACD-8754"
"cdv-2644"          →  1. "CDV-2644"         →  "CDV2644", "CDV 2644"  
"GEFD24617"         →  1. "GEFD24617"        →  "GEFD-24617", "GEFD 24617"
"B0001234 02"       →  1. "B0001234 02"      →  "B000123402", "B0001234-02"
```

#### **Enhanced Search Strategy**
1. **Original First**: Always tries your exact input first (most important!)
2. **Format Variations**: Tries with/without spaces and hyphens automatically
3. **Common Patterns**: Tests typical catalog number formats
4. **Comprehensive Coverage**: Up to 6+ variations per catalog number
5. **Track Validation**: Only shows releases matching your CD's track count
6. **Graceful Fallback**: Falls back to artist/album search if catalog fails

#### **User Validation Process**
1. **Format Validation**: Checks catalog number format before searching
2. **Search Results**: Shows all matching releases with track counts
3. **Multiple Matches**: User selects correct release if multiple found
4. **Confirmation**: Displays found metadata for user verification
5. **Fallback Option**: Can skip catalog search and use manual entry

#### **When to Use Catalog Numbers**
- **Reissues/Remasters**: Multiple versions of same album exist
- **Import CDs**: Unusual or foreign releases  
- **Compilations**: Generic titles like "Greatest Hits"
- **Soundtracks**: Multiple soundtrack versions exist
- **Box Sets**: Complex multi-disc releases
- **Rare/Obscure**: Hard to find releases with unusual metadata

#### **Error Handling**
- **Invalid Format**: Prompts for re-entry with format guidance
- **No Results**: Gracefully falls back to standard search after trying all variations
- **Multiple Matches**: User selection with detailed information
- **Network Issues**: Continues with manual metadata entry
- **Format Preservation**: Always tries your original input first, then variations
- **Comprehensive Search**: Tries 3-6 format variations automatically

### Multi-Disc Album Support
- **File naming**: Uses `Disc-Track` format (e.g., `01-01`, `02-03`)
- **Single discs**: Automatically use `01-XX` format for consistency
- **Multi-disc sets**: Specify disc number during initial setup
- **Metadata**: Includes proper disc number and total disc count in FLAC tags

### Example Output Structure
```
output/
├── Blur/
│   └── The Magic Whip/
│       ├── 01-01. Lonesome Street.flac
│       ├── 01-02. New World Towers.flac
│       ├── 01-03. Go Out.flac
│       ├── cover.jpg
│       └── rip_info.json
├── Hole/
│   └── Celebrity Skin/
│       ├── 01-01. Celebrity Skin.flac
│       ├── 01-02. Awful.flac
│       ├── cover.jpg
│       └── rip_info.json
├── The Doobie Brothers/
│   └── Minute By Minute/
│       ├── 01-01. Here to Love You.flac
│       ├── 01-02. What a Fool Believes.flac
│       ├── cover.jpg
│       └── rip_info.json
├── Various Artists/
│   └── Now That's What I Call Music! 25/
│       ├── 01-01. Spice Girls - Wannabe.flac
│       ├── 01-02. Oasis - Don't Look Back in Anger.flac
│       ├── 01-03. Blur - Song 2.flac
│       ├── cover.jpg
│       └── rip_info.json
└── Soundtracks/
    ├── Guardians of the Galaxy Soundtrack/
    │   ├── 01-01. Blue Swede - Hooked on a Feeling.flac
    │   ├── 01-02. Raspberries - Go All the Way.flac
    │   ├── 01-03. Norman Greenbaum - Spirit in the Sky.flac
    │   ├── cover.jpg
    │   └── rip_info.json
    └── Higher Learning: Music From the Motion Picture/
        ├── 01-01. Ice Cube - Higher.flac
        ├── 01-02. Ice Cube - Something to Think About.flac
        ├── 01-08. Unknown Artist - My New Friend.flac
        ├── cover.jpg
        └── rip_info.json
```

## Key Features

### **Reliability First**
- **Independent phases**: Ripping success doesn't depend on metadata
- **Error recovery**: Continues processing even if individual tracks fail
- **Graceful degradation**: Manual fallback when automatic systems fail

### **Smart Metadata Integration**
- **MusicBrainz integration**: Automatic track and artist information lookup
- **Track count validation**: Ensures metadata matches your actual CD
- **Cover art download**: Automatic album art from Cover Art Archive
- **Comprehensive tagging**: Proper FLAC metadata including MusicBrainz IDs

### **Organized Output**
- **Nested structure**: `output/Artist/Album/` for easy browsing
- **Proper naming**: Files named with actual track titles
- **Space-friendly**: Preserves natural spacing in folder/file names
- **Audit trail**: `rip_info.json` preserves ripping session details

### **Production Ready**
- **Detailed logging**: Complete session logs for troubleshooting
- **Progress tracking**: Real-time status updates during ripping
- **Error handling**: Comprehensive error reporting and recovery
- **Scalable**: Designed for processing hundreds of CDs

### **Cover Art Management**
- **Missing cover detection**: Scan entire collection for albums without cover art
- **Discogs API integration**: Automatic cover search and download with authentication
- **Interactive selection**: Choose from multiple cover options with confidence scoring
- **Fallback options**: Manual download guidance and alternative sources (MusicBrainz, Google Images)
- **FLAC embedding**: Automatically adds cover art to all FLAC files
- **Metadata updates**: Updates both cover files and rip_info.json records

### **Metadata Enrichment**
- **Industry standards**: 5-level metadata hierarchy (Required, Standard, MusicBrainz, Extended, Technical)
- **Batch processing**: Enriches entire collection with comprehensive metadata
- **API integration**: MusicBrainz and Discogs data for accurate information
- **Safe operation**: Validation and backup systems protect existing data
- **Progress tracking**: Real-time updates during enrichment process

## Cover Art Management

### Find Missing Covers

Scan your collection for albums missing cover art:

```bash
python3 find_missing_covers.py output
```

### Discogs Cover Manager

Automatically search and download covers using the Discogs API:

```bash
python3 discogs_cover_manager.py output
```

**Setup Process:**
1. Get a Discogs personal access token from https://www.discogs.com/settings/developers
2. Create a new token with name "CD Ripper Cover Art"
3. Run the script - it will prompt for authentication on first use
4. Token is securely saved for future sessions

**Features:**
- Interactive search with confidence scoring
- Multiple fallback options for blocked images
- Automatic FLAC metadata embedding
- Updates rip_info.json with cover information

### Simple Cover Manager

For manual cover addition when you already have cover images:

```bash
python3 simple_cover_manager.py output
```

**Features:**
- Interactive album-by-album processing
- Automatic image validation and resizing
- Supports JPG and PNG formats
- Embeds covers into all FLAC files

### Metadata Enrichment

Enrich existing albums with comprehensive industry-standard metadata:

```bash
python3 enrich_metadata.py
```

**Metadata Levels:**
- **Level 1 (Required)**: ALBUM, ALBUMARTIST, ARTIST, TITLE, TRACKNUMBER, DATE
- **Level 2 (Standard)**: DISCNUMBER, TOTALDISCS, TOTALTRACKS, GENRE
- **Level 3 (MusicBrainz)**: MUSICBRAINZ_ALBUMID, DISCOGS_RELEASE_ID
- **Level 4 (Extended)**: CATALOGNUMBER, COUNTRY, ORGANIZATION, STYLE, MEDIATYPE
- **Level 5 (Technical)**: ENCODER, WWW, sorting fields

## Troubleshooting

### Artist Name Preferences

#### **Language Choice**
When MusicBrainz returns artist names in different languages/scripts:
- **User Choice**: System detects when MusicBrainz name differs significantly from your input
- **Example**: Your input "Tchaikovsky" vs MusicBrainz "Пётр Ильич Чайковский" (Russian)
- **Interactive Prompt**: Choose between your input or MusicBrainz version
- **Default**: Uses your original input to maintain consistent English naming

### Directory Management

#### **Automatic Cleanup**
- **Smart Reorganization**: When metadata changes artist names, files move to correct directories
- **Empty Directory Removal**: Automatically removes empty directories after reorganization
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

#### **Quality Standards**
- **Resolution**: Prefers images ≥800x800 pixels
- **File Size**: Optimizes large images while preserving quality
- **Format**: Converts to JPEG for space efficiency
- **Validation**: Verifies image integrity before saving

### Manual Cover Management
```bash
# Manual cover art addition tool
python3 manual_cover_manager.py output
```

**For special cases requiring manual intervention:**
- **File-based Addition**: Add covers from local image files
- **Quality Validation**: Automatic image validation and resizing
- **FLAC Integration**: Embeds artwork into all album FLAC files
- **Metadata Updates**: Updates rip_info.json automatically

### Cover Art Validation
```bash
# Validate existing cover art paths in rip_info.json files
python3 validate_cover_art.py output
```

**Ensures cover art metadata accuracy:**
- **Path Verification**: Checks if cover_art paths in rip_info.json exist
- **Automatic Correction**: Updates paths to actual cover art files
- **Missing Detection**: Identifies albums with broken cover art references
- **Batch Processing**: Fixes multiple albums efficiently

### Integration with Ripping Process

**During CD ripping, cover art is handled automatically:**
1. **MusicBrainz Cover Art Archive**: First priority for automatic download
2. **Embedded in FLAC**: Cover art embedded directly in audio files
3. **File Storage**: Saved as `cover.jpg` in album directory
4. **Metadata Tracking**: Recorded in `rip_info.json` for future reference

**Post-rip cover art management handles:**
- Albums where automatic download failed
- Higher quality cover art replacement
- Missing covers for existing albums
- Cover art quality improvements

### Common Cover Art Issues

- **Missing API Token**: Script guides through Discogs token setup
- **Rate Limiting**: Automatic throttling prevents API blocks
- **Download Failures**: Multiple fallback sources and manual options
- **Cross-device Errors**: Fixed file moving across filesystem boundaries
- **Low Quality Images**: Quality assessment identifies improvement candidates
- **Inconsistent Embedding**: Tools verify and fix FLAC embedded artwork

## Future Enhancements (Parts 2 & 3)

- **Part 2**: Automated upload to AWS S3 for cloud storage
- **Part 3**: Local compression to M4A format with FLAC cleanup