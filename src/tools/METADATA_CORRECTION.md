# Metadata Correction Tool

## Overview

The Metadata Correction Tool (`fix-metadata`) helps fix albums that received incorrect MusicBrainz metadata during the CD ripping process. This commonly happens when:

1. Multiple albums have similar names
2. The automatic MusicBrainz matching picks the wrong release
3. There are different regional releases with the same title
4. Soundtracks or compilations get confused with other albums

## Features

- **Interactive Search**: Browse alternative MusicBrainz matches for an album
- **Direct MBID Application**: Apply a specific MusicBrainz ID if you know the correct one
- **Preview Mode**: See what changes would be made before applying them
- **Automatic File Renaming**: Rename FLAC files to match corrected metadata
- **Backup Creation**: Creates backup of rip_info.json before making changes
- **Comprehensive Metadata**: Updates all metadata fields including MusicBrainz IDs

## Usage

### Basic Interactive Mode
```bash
python3 cd_manager.py fix-metadata "/path/to/album"
```
This will search for alternative MusicBrainz matches and let you choose the correct one.

### Custom Search Query
```bash
python3 cd_manager.py fix-metadata "/path/to/album" --search "Artist - Album Title"
```
Use a custom search query to find better matches.

### Direct MBID Application
```bash
python3 cd_manager.py fix-metadata "/path/to/album" --mbid "musicbrainz-id"
```
Apply a specific MusicBrainz ID directly (useful if you know the correct MBID).

### Apply Changes
```bash
python3 cd_manager.py fix-metadata "/path/to/album" --apply
```
Actually make the changes (without --apply, it's preview mode only).

### Apply Changes and Rename Files
```bash
python3 cd_manager.py fix-metadata "/path/to/album" --apply --rename
```
Apply changes and also rename FLAC files to match the corrected metadata.

## Complete Example Workflow

### Step 1: Identify the Problem
You notice an album has wrong metadata. For example, the Armageddon soundtrack was matched to a drum & bass compilation instead of the movie soundtrack.

### Step 2: Preview Available Options
```bash
python3 cd_manager.py fix-metadata "/path/to/Armageddon"
```

This shows:
- Current metadata information
- Number of FLAC files
- Alternative MusicBrainz matches
- Track count comparison (✅ for matches, ❌ for mismatches)

### Step 3: Select Correct Release
The tool displays options like:
```
1. Armageddon: The Album
   Artist: Various Artists
   Date: 1998-06-23
   Country: US
   Label: Columbia
   Tracks: 14 ✅
   MBID: 20e562ef-c7f5-4846-8b16-65b12e06ef35
```

Enter the number of the correct release.

### Step 4: Apply the Correction
```bash
python3 cd_manager.py fix-metadata "/path/to/Armageddon" --apply --rename
```

## What Gets Updated

### rip_info.json
- Album title, artist, date
- MusicBrainz ID (MBID)
- Track information with correct titles and artists
- Adds correction timestamp and tool info
- Creates backup (.json.backup)

### FLAC Files Metadata
- **ALBUM**: Album title
- **ALBUMARTIST**: Album artist  
- **DATE**: Release date
- **MUSICBRAINZ_ALBUMID**: Release MBID
- **TITLE**: Correct track titles
- **ARTIST**: Correct track artists
- **TRACKNUMBER**: Disc-Track format (01-01, 01-02, etc.)
- **MUSICBRAINZ_TRACKID**: Track MBIDs
- **TOTALTRACKS**: Total track count
- **TOTALDISCS**: Total disc count

### File Names (with --rename)
Files are renamed from:
```
01-01. Unknown Artist - Contact.flac
```
To:
```
01-01. Aerosmith - I Don't Want to Miss a Thing.flac
```

## Error Recovery

### Backup Files
The tool automatically creates a backup of your rip_info.json:
```
rip_info.json.backup
```

### Undo Changes
If something goes wrong, you can restore from backup:
```bash
cd "/path/to/album"
cp rip_info.json.backup rip_info.json
```

Then re-run the enrich command:
```bash
python3 cd_manager.py enrich "/path/to/album" --apply
```

## Common Use Cases

### Case 1: Wrong Album Match
**Problem**: Your "Greatest Hits" album was matched to a different artist's greatest hits.
**Solution**: Use interactive mode to find the correct artist's release.

### Case 2: Wrong Regional Release
**Problem**: Your US CD was matched to a European release with different track listing.
**Solution**: Look for releases with matching country and track count.

### Case 3: Soundtrack Confusion
**Problem**: Movie soundtrack matched to a different movie with similar name.
**Solution**: Check release dates to match the correct movie year.

### Case 4: Known Correct MBID
**Problem**: You know the exact MusicBrainz ID that should be used.
**Solution**: Use --mbid parameter to apply directly.

## Tips

1. **Check Track Count**: Always look for releases with matching track counts (✅)
2. **Verify Release Date**: Movie soundtracks should match the movie year
3. **Check Country**: Your CD region should usually match the release country
4. **Preview First**: Always run without --apply first to see what changes
5. **Use Barcode**: If you have the CD case, the barcode can help identify the exact release

## Integration with Other Tools

After using fix-metadata, you can use other tools:

- **enrich**: Add additional metadata fields
- **batch-covers**: Update cover art to match corrected album
- **validate**: Check that all metadata is consistent

This tool provides a comprehensive solution for fixing metadata mistakes and ensures your music collection has accurate, consistent information.