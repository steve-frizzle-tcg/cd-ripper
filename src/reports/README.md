# Collection Analysis & Reporting Documentation

## cover_art_report.py - Comprehensive Collection Analysis

Detailed analysis tool that provides comprehensive statistics and quality assessment of your entire music collection.

### Features
- Collection-wide statistics
- Cover art quality assessment
- Missing content identification
- Format analysis
- Issue detection and reporting

### Usage
```bash
python3 cd_manager.py report
python3 cd_manager.py report --directory /path/to/collection
```

### Report Sections

#### Summary Statistics
- Total albums count
- Coverage percentages (file art, FLAC embedded art)
- Missing content breakdown
- Average image dimensions
- Format distribution

#### Missing Cover Art
- Complete list of albums without any cover art
- File counts and paths for reference

#### Quality Assessment
Albums categorized by quality:
- **Excellent**: 800x800+, 100KB+ file size
- **Good**: 600x600+, 50KB+ file size  
- **Fair**: 400x400+ pixels
- **Poor**: 200x200+ pixels
- **Very Poor**: Under 200x200 pixels

#### Issue Detection
- Albums with inconsistent FLAC embedding
- Low-quality cover art identification
- Format inconsistencies
- File size anomalies

### Example Output
```
📊 Cover Art Analysis Summary
==================================================
Total Albums: 316
Albums with cover files: 289 (91.5%)
Albums with FLAC embedded art: 307 (97.2%)
Albums with both: 289 (91.5%)
Albums missing all cover art: 9

Average cover art size: 987x980

Cover art formats:
  JPEG: 273 (94.5%)
  PNG: 16 (5.5%)
```

## find_missing_covers.py - Missing Cover Scanner

Focused tool for identifying albums that lack cover art entirely.

### Features
- Quick scanning for missing covers
- File-based and embedded art detection
- Artist/album organization
- Path information for easy access

### Usage
```bash
python3 cd_manager.py find-missing
```

### Output Format
Lists albums missing cover art in format:
```
❌ Albums Missing Cover Art (9):
==================================================
• Artist Name / Album Name
  📁 12 FLAC files
```

### Integration
Perfect for:
- Quick status checks
- Feeding into batch processing tools
- Identifying priority albums for cover art addition
- Collection maintenance planning
