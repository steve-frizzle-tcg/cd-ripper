# FLAC Metadata Standards Documentation

This document defines the metadata standards for FLAC files in the CD ripping collection, ensuring consistency and compatibility with music industry standards.

## Metadata Standard Levels

### Level 1: Required Fields (Always Present)
These fields must be present in every FLAC file:

- **ALBUM** - Album title (e.g., "Dark Side of the Moon")
- **ALBUMARTIST** - Album artist (e.g., "Pink Floyd" or "Various Artists" for compilations)
- **ARTIST** - Track artist (individual track performer, may differ from album artist)
- **TITLE** - Track title (e.g., "Money")
- **TRACKNUMBER** - Track number in disc-track format (e.g., "01-05" for disc 1, track 5)
- **DATE** - Release date (prefer full date YYYY-MM-DD, fallback to year YYYY)

### Level 2: Standard Fields (Should Be Present When Available)
These fields should be included when the information is available:

- **DISCNUMBER** - Disc number for multi-disc releases (e.g., "1", "2")
- **TOTALDISCS** - Total number of discs in release (e.g., "2")
- **TOTALTRACKS** - Total number of tracks in entire release
- **GENRE** - Music genre (e.g., "Progressive Rock", "Jazz", "Classical")
- **ALBUMARTISTSORT** - Album artist sort name (e.g., "Beatles, The")
- **ARTISTSORT** - Track artist sort name for proper alphabetization
- **ALBUMSORT** - Album sort name (for articles like "The", "A")
- **TITLESORT** - Title sort name

### Level 3: MusicBrainz Identification Fields
Essential for music database integration and identification:

- **MUSICBRAINZ_ALBUMID** - Release MBID (UUID format)
- **MUSICBRAINZ_ARTISTID** - Album artist MBID
- **MUSICBRAINZ_TRACKID** - Recording MBID (identifies the specific recording)
- **MUSICBRAINZ_RELEASETRACKID** - Track MBID (identifies track on this release)
- **MUSICBRAINZ_RELEASEGROUPID** - Release group MBID (groups different releases of same album)

### Level 4: Extended Metadata Fields
Additional information for comprehensive cataloging:

- **LABEL** - Record label (e.g., "Columbia Records", "Blue Note")
- **CATALOGNUMBER** - Catalog number (e.g., "CDP 7 46001 2", "B0000123-02")
- **BARCODE** - UPC/EAN barcode number
- **COUNTRY** - Release country (ISO 3166-1 alpha-2, e.g., "US", "GB", "DE")
- **MEDIA** - Media format (e.g., "CD", "Vinyl", "Digital Media")
- **STATUS** - Release status (e.g., "Official", "Bootleg", "Promotional")
- **SCRIPT** - Script used (e.g., "Latn", "Cyrl", "Jpan")
- **LANGUAGE** - Language (ISO 639-3, e.g., "eng", "deu", "jpn")
- **ASIN** - Amazon Standard Identification Number
- **ISRC** - International Standard Recording Code (per track)
- **ORIGINALDATE** - Original release date (for reissues)
- **ORIGINALYEAR** - Original release year

### Level 5: Technical Fields
Audio and encoding information:

- **ENCODING** - Encoding information
- **ENCODER** - Software/hardware encoder used (e.g., "FLAC 1.3.4")
- **ENCODERSETTINGS** - Encoder settings used

## Field Format Standards

### Track Numbering
- Use **disc-track format**: `DD-TT` (e.g., "01-05", "02-12")
- Always zero-pad to 2 digits
- Single disc releases use "01-XX" format

### Dates
- **Primary format**: YYYY-MM-DD (ISO 8601)
- **Fallback**: YYYY (year only)
- **Invalid**: MM/DD/YYYY, DD.MM.YYYY, or other non-ISO formats

### Artist Names
- Use **official artist names** from MusicBrainz when available
- For compilations: ALBUMARTIST = "Various Artists"
- Individual track artists preserved in ARTIST field
- Sort names follow "Last, First" convention

### Album Types
- **Regular Album**: Single artist, standard album
- **Soundtrack**: Movie/TV/Game soundtracks (goes in Soundtracks/ directory)
- **Compilation**: Various artists collections (ALBUMARTIST = "Various Artists")

## Cover Art Standards

### Embedded Cover Art
- **Required**: Front cover embedded in all FLAC files
- **Format**: JPEG preferred, PNG acceptable
- **Resolution**: Minimum 500x500, prefer 1000x1000 or higher
- **Type**: Picture type 3 (Cover - front)

### External Cover Art Files
- **Filename**: `cover.jpg` in album directory
- **Purpose**: Backup and file browser display
- **Sync**: Must match embedded cover art

## Quality Assurance

### Validation Rules
1. All Level 1 (Required) fields must be present and non-empty
2. Track numbers must be sequential and properly formatted
3. Disc/track totals must be accurate
4. MusicBrainz IDs must be valid UUIDs if present
5. Dates must follow ISO 8601 format
6. Cover art must be embedded and high quality

### Consistency Checks
1. ALBUMARTIST consistent across all tracks in album
2. ALBUM title consistent across all tracks
3. TOTALTRACKS matches actual number of files
4. DISCNUMBER/TOTALDISCS consistent within multi-disc sets
5. Track numbering sequential without gaps

## Implementation

### Automated Enrichment
The `enrich_metadata.py` script automatically:
1. Validates existing metadata against standards
2. Enriches with MusicBrainz data when available
3. Applies consistent formatting
4. Adds missing required fields
5. Embeds cover art if missing

### Manual Overrides
Certain fields may be manually overridden:
- Artist name preferences (English vs native script)
- Album titles (common vs official names)
- Genre classifications
- Custom sort names

### Backward Compatibility
- Existing non-standard fields are preserved
- New standards applied additively
- Migration scripts maintain data integrity
- Rollback capability for standard changes

## Examples

### Regular Album (Single Artist)
```
ALBUM=Dark Side of the Moon
ALBUMARTIST=Pink Floyd
ARTIST=Pink Floyd
TITLE=Money
TRACKNUMBER=01-06
DISCNUMBER=1
TOTALDISCS=1
TOTALTRACKS=10
DATE=1973-03-01
MUSICBRAINZ_ALBUMID=a3b5c2d1-1234-5678-9abc-def012345678
```

### Compilation Album (Various Artists)
```
ALBUM=Now That's What I Call Music! 50
ALBUMARTIST=Various Artists
ARTIST=Britney Spears
TITLE=Toxic
TRACKNUMBER=01-03
DISCNUMBER=1
TOTALDISCS=2
TOTALTRACKS=42
DATE=2004-07-26
MUSICBRAINZ_ALBUMID=b4c6d3e2-2345-6789-abcd-ef0123456789
```

### Soundtrack
```
ALBUM=The Matrix: Music from the Motion Picture
ALBUMARTIST=Various Artists
ARTIST=Rob Dougan
TITLE=Clubbed to Death
TRACKNUMBER=01-08
DISCNUMBER=1
TOTALDISCS=1
TOTALTRACKS=12
DATE=1999-03-30
MUSICBRAINZ_ALBUMID=c5d7e4f3-3456-789a-bcde-f01234567890
```

## Maintenance

### Regular Tasks
1. **Validation runs**: Monthly checks for standard compliance
2. **MusicBrainz updates**: Quarterly enrichment with latest data
3. **New standard adoption**: Update scripts when standards evolve
4. **Quality audits**: Sample checking of metadata accuracy

### Version Control
- Standards versioned with semantic versioning (v1.0.0)
- Migration scripts for standard updates
- Changelog maintained for all standard modifications
- Backward compatibility ensured for at least 2 major versions

---

**Last Updated**: September 16, 2025  
**Standard Version**: 1.0.0  
**Next Review**: December 2025
