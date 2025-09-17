#!/bin/bash

# Comprehensive script to rename all album cover art files to cover.jpg
# This script handles:
# 1. JPG files with extensions
# 2. PNG, GIF, BMP files with extensions  
# 3. Image files without extensions

echo "Starting comprehensive cover art renaming..."

# Function to rename files with a given find pattern
rename_files() {
    local find_cmd="$1"
    local description="$2"
    
    echo "Processing $description..."
    
    eval "$find_cmd" | while read -r file; do
        # Handle the case where we're getting output from 'file' command
        if [[ "$file" == *": "* ]]; then
            file_path=$(echo "$file" | cut -d: -f1)
        else
            file_path="$file"
        fi
        
        # Get the directory containing the image file
        dir=$(dirname "$file_path")
        
        # Get the current filename
        current_name=$(basename "$file_path")
        
        # Skip if already named cover.jpg or cover (without extension)
        if [[ "$current_name" == "cover.jpg" ]] || [[ "$current_name" == "cover" ]]; then
            echo "Skipping (already named correctly): $file_path"
            continue
        fi
        
        # New path with cover.jpg
        new_path="$dir/cover.jpg"
        
        # Check if cover.jpg already exists in this directory
        if [[ -f "$new_path" ]]; then
            echo "Warning: cover.jpg already exists in $dir, skipping $current_name"
            continue
        fi
        
        # Rename the file
        mv "$file_path" "$new_path"
        echo "Renamed: $current_name -> cover.jpg in $dir"
    done
}

# 1. Handle JPG files with extensions
rename_files 'find "/home/steve/FLAC" -name "*.jpg" -type f ! -name "cover.jpg"' "JPG files with extensions"

# 2. Handle other image files with extensions (PNG, GIF, BMP, JPEG)
rename_files 'find "/home/steve/FLAC" -type f \( -iname "*.png" -o -iname "*.jpeg" -o -iname "*.gif" -o -iname "*.bmp" \) ! -name "cover.*"' "other image files with extensions"

# 3. Handle extensionless image files
rename_files 'find "/home/steve/FLAC" -type f ! -name "*.*" -exec file {} \; | grep -i "image\|jpeg\|png\|gif\|bmp"' "extensionless image files"

# 4. Handle files with periods in filename but no actual extension (edge case)
echo "Checking for files with periods in names that might be extensionless image files..."
find "/home/steve/FLAC" -type f -name "*.*" | while read -r file; do
    # Check if the file has a typical extension
    if [[ ! "$file" =~ \.(flac|mp3|wav|jpg|jpeg|png|gif|bmp|txt|log|cue|m3u|nfo)$ ]]; then
        # Check if it's an image file
        file_type=$(file "$file" 2>/dev/null | grep -i "image\|jpeg\|png\|gif\|bmp")
        if [[ -n "$file_type" ]]; then
            # Get the directory containing the image file
            dir=$(dirname "$file")
            
            # Get the current filename
            current_name=$(basename "$file")
            
            # Skip if already named cover.jpg
            if [[ "$current_name" == "cover.jpg" ]]; then
                echo "Skipping (already named correctly): $file"
                continue
            fi
            
            # New path with cover.jpg
            new_path="$dir/cover.jpg"
            
            # Check if cover.jpg already exists in this directory
            if [[ -f "$new_path" ]]; then
                echo "Warning: cover.jpg already exists in $dir, skipping $current_name"
                continue
            fi
            
            # Rename the file
            mv "$file" "$new_path"
            echo "Renamed: $current_name -> cover.jpg in $dir"
        fi
    fi
done

echo ""
echo "Renaming complete!"
echo "Total cover.jpg files: $(find /home/steve/FLAC -name "cover.jpg" -type f | wc -l)"
echo "Remaining image files not named cover.jpg: $(find /home/steve/FLAC -type f \( -iname "*.jpg" -o -iname "*.jpeg" -o -iname "*.png" -o -iname "*.gif" -o -iname "*.bmp" \) ! -name "cover.jpg" | wc -l)"
