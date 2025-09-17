# Cover Art Management Documentation

## discogs_cover_manager.py - Interactive Discogs Integration

Primary cover art management tool with Discogs API integration for high-quality album artwork.

### Features
- Discogs API integration with authentication
- Interactive search and preview
- Multiple fallback sources (official releases, alternate versions)
- Rate limiting and error handling
- Quality assessment and validation
- Automatic FLAC embedding

### Setup
Create `~/.config/discogs/config.ini`:
```ini
[discogs]
user_token = your_discogs_user_token_here
```

### Usage
```bash
python3 cd_manager.py covers
```

## batch_cover_processor.py - Automated Batch Processing

Automated tool for processing multiple albums missing cover art.

### Features
- Automatic Discogs searching
- Quality filtering
- Batch processing with limits
- Progress tracking
- Error handling and logging

### Usage
```bash
# Process all albums automatically
python3 cd_manager.py batch-covers output --auto

# Limit to 10 albums
python3 cd_manager.py batch-covers output --limit 10
```

## manual_cover_manager.py - Manual Cover Addition

Tool for manually adding cover art when automated tools fail.

### Features
- Manual image file selection
- Format conversion (PNG to JPEG)
- Size optimization
- FLAC embedding
- Quality validation

### Usage
Interactive mode guides you through the process.

## manual_cover_updater.py - Cover Art Replacement

Specialized tool for replacing existing cover art with new images.

### Features
- Replace existing cover files
- Update FLAC embedded art
- Format conversion
- Size optimization
- Metadata updates

### Usage
```bash
python3 cd_manager.py replace-cover "output/Artist/Album" new_cover.jpg
```

## simple_cover_manager.py - Basic Cover Management

Simplified interface for basic cover art operations.

### Features
- Simple search interface
- Basic quality checks
- Quick embedding
- Minimal configuration required

### Best Practices

1. **Quality Standards**
   - Minimum 600x600 pixels
   - JPEG format preferred for size efficiency
   - File size 50KB-500KB optimal

2. **Naming Conventions**
   - `cover.jpg` for album directories
   - Consistent naming across collection

3. **Workflow**
   - Use automated tools first (batch_cover_processor)
   - Fall back to interactive search (discogs_cover_manager)  
   - Manual intervention only when needed

4. **Quality Assessment**
   - Excellent: 800x800+, 100KB+
   - Good: 600x600+, 50KB+
   - Fair: 400x400+
   - Poor: 200x200+
