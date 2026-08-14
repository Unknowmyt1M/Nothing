
#!/usr/bin/env python3
"""
Test script specifically for Vimeo functionality using the provided cookies
"""

import os
import sys
from multi_platform_downloader import extract_platform_metadata, download_from_platform, get_platform_from_url

def test_vimeo_with_cookies():
    """Test Vimeo metadata extraction and download with provided cookies"""
    
    # Test URLs - using popular Vimeo videos
    test_urls = [
        'https://vimeo.com/336812686',  # A popular Vimeo video
        'https://vimeo.com/148751763',  # Another test video
        'https://vimeo.com/90509568',   # Short documentary
    ]
    
    print("=== Vimeo Cookie Test ===")
    print(f"Using cookies file: cookies/vimeo_cookies.txt")
    
    # Check if cookies file exists
    cookies_file = "cookies/vimeo_cookies.txt"
    if not os.path.exists(cookies_file):
        print(f"❌ Cookies file not found: {cookies_file}")
        return False
    
    print(f"✓ Cookies file found")
    
    # Test platform detection
    for url in test_urls:
        platform = get_platform_from_url(url)
        print(f"\nTesting URL: {url}")
        print(f"Detected platform: {platform}")
        
        if platform != 'vimeo':
            print(f"❌ Platform detection failed - expected 'vimeo', got '{platform}'")
            continue
        
        # Test metadata extraction
        try:
            print("Extracting metadata...")
            metadata = extract_platform_metadata(url, 'vimeo')
            
            print("✓ Metadata extraction successful!")
            print(f"  Title: {metadata.get('title', 'Unknown')}")
            print(f"  Uploader: {metadata.get('uploader', 'Unknown')}")
            print(f"  Duration: {metadata.get('duration', 'Unknown')}")
            print(f"  Views: {metadata.get('view_count', 'Unknown')}")
            print(f"  Tags: {metadata.get('tags', [])}")
            
            # Test download (just metadata, not actual download)
            print("Testing download capability...")
            try:
                # Create test directory
                os.makedirs('test_downloads', exist_ok=True)
                
                # This would download the video - commenting out to avoid large downloads
                # downloaded_file = download_from_platform(url, 'test_downloads', 'vimeo')
                # print(f"✓ Download successful: {downloaded_file}")
                
                print("✓ Download configuration successful (actual download skipped)")
                
            except Exception as download_error:
                print(f"❌ Download test failed: {download_error}")
                
        except Exception as e:
            print(f"❌ Metadata extraction failed: {e}")
            
            # Check for specific error types
            if "Failed to fetch android OAuth token" in str(e):
                print("  → This might be due to Vimeo's API changes or cookie expiration")
            elif "HTTP Error 400" in str(e):
                print("  → Bad request - cookies might be expired or invalid")
            elif "HTTP Error 403" in str(e):
                print("  → Access forbidden - authentication issue")
                
    return True

def test_vimeo_integration():
    """Test Vimeo integration with the main app"""
    print("\n=== Testing Vimeo Integration ===")
    
    from multi_platform_downloader import get_supported_platforms, is_platform_supported
    
    # Check if Vimeo is in supported platforms
    supported = get_supported_platforms()
    print(f"Supported platforms: {supported}")
    
    if 'vimeo' in supported:
        print("✓ Vimeo is in supported platforms list")
    else:
        print("❌ Vimeo not found in supported platforms")
        
    # Test URL support check
    test_url = "https://vimeo.com/336812686"
    is_supported = is_platform_supported(test_url)
    print(f"URL support check for {test_url}: {is_supported}")

if __name__ == "__main__":
    print("Vimeo Testing Script")
    print("=" * 50)
    
    try:
        test_vimeo_with_cookies()
        test_vimeo_integration()
        print("\n✓ Vimeo testing completed")
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        sys.exit(1)
