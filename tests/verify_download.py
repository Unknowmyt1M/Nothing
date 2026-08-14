import os
import sys

# Add root folder to import paths
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend.platforms import download_from_platform, get_platform_from_url

def main():
    print("=== Testing Backend Download Pipeline ===")
    
    # 2MB sample video link
    test_url = "https://placeholdervideo.dev/1920x1080"
    platform = get_platform_from_url(test_url)
    print(f"Detected platform: {platform}")
    
    output_dir = "test_downloads"
    os.makedirs(output_dir, exist_ok=True)
    
    print(f"Downloading video from {test_url} to folder: {output_dir}...")
    
    try:
        def progress_callback(d):
            if d.get('status') == 'downloading':
                pct = d.get('downloaded_bytes', 0) / (d.get('total_bytes') or 1) * 100
                print(f"  Progress: {pct:.1f}%")
                
        filename = download_from_platform(test_url, output_dir, platform, progress_callback)
        print(f"[OK] Download completed successfully!")
        print(f"[OK] Saved as: {filename}")
        print(f"[OK] File size: {os.path.getsize(filename) / (1024 * 1024):.2f} MB")
        
        # Clean up
        if os.path.exists(filename):
            os.remove(filename)
            print("[OK] Temporary test file removed.")
            
    except Exception as e:
        print(f"[ERROR] Download failed with error: {e}")

if __name__ == "__main__":
    main()

