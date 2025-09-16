#!/usr/bin/env python3
"""
Test script to demonstrate the new artist name choice feature.
This simulates what would happen when ripping the Tchaikovsky CD.
"""

def simulate_artist_choice():
    original_artist = "Tchaikovsky"
    mb_artist = "Пётр Ильич Чайковский"
    
    print("=== Artist Name Choice Simulation ===")
    print(f"User entered: '{original_artist}'")
    print(f"MusicBrainz found: '{mb_artist}'")
    print()
    
    # This is what the user would see
    print("🎵 Artist Name Choice:")
    print(f"   1. Your input: '{original_artist}' (keeps English/familiar name)")
    print(f"   2. MusicBrainz: '{mb_artist}' (official database name)")
    print(f"   Note: This affects folder organization (output/{original_artist}/ vs output/{mb_artist}/)")
    
    # Simulate choosing option 1 (default)
    choice = "1"  # User chooses to keep English name
    
    if choice == "2":
        chosen_artist = mb_artist
        folder_path = f"output/{mb_artist}/The Very Best of Tchaikovsky/"
    else:
        chosen_artist = original_artist
        folder_path = f"output/{original_artist}/The Very Best of Tchaikovsky/"
    
    print(f"\nResult:")
    print(f"✅ Chosen artist: '{chosen_artist}'")
    print(f"📁 Folder location: {folder_path}")
    print(f"🎵 Files will have proper MusicBrainz metadata but English folder structure")

if __name__ == "__main__":
    simulate_artist_choice()
