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
3. **Enter basic info**: Artist/album details based on type, year (optional), disc number (for multi-disc albums)
4. **Automatic ripping**: Script rips all tracks (5-10 minutes typical)
5. **Metadata enhancement**: Automatic MusicBrainz lookup with Various Artists support
6. **Completion**: Files organized in `output/Artist/Album/` directory

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

## Troubleshooting

### Common Issues
- **No CD detected**: Check CD drive connection and permissions
- **MusicBrainz failures**: Script continues with manual metadata entry
- **Track ripping errors**: Individual track failures don't stop the process
- **Permission errors**: Ensure user has access to CD drive (`/dev/cdrom`)
- **Dialogue tracks**: Movie soundtracks may include dialogue/scene audio with problematic metadata - automatically cleaned to "Unknown Artist"
- **Invalid artist names**: Malformed MusicBrainz data (like " & ") is automatically cleaned or replaced with "Unknown Artist"

### Log Files
Check `logs/rip_cd_YYYYMMDD_HHMMSS.log` for detailed error information.

## Future Enhancements (Parts 2 & 3)

- **Part 2**: Automated upload to AWS S3 for cloud storage
- **Part 3**: Local compression to M4A format with FLAC cleanup