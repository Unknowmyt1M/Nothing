
#!/usr/bin/env python3
"""
Test script for direct URL functionality
"""

from multi_platform_downloader import extract_platform_metadata, get_platform_from_url, get_platform_display_name

def test_direct_url_detection():
    """Test direct URL detection using new HTTP header method"""
    print("=== Testing Direct URL Detection (HTTP Headers) ===")
    
    # Import the new function
    from multi_platform_downloader import is_direct_download_url
    
    test_urls = [
        'https://sample-videos.com/zip/10/mp4/SampleVideo_720x480_1mb.mp4',
        'https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/BigBuckBunny.mp4',
        'https://youtube.com/watch?v=abc123',  # Should NOT be direct
        'https://www.instagram.com/p/test/',   # Should NOT be direct
        'https://file-examples.com/storage/fe6d99b7673e9e351ac5a1b/2017/10/file_example_MP4_480_1_5MG.mp4'
    ]
    
    for url in test_urls:
        print(f"Testing: {url}")
        
        # Test new HTTP header method
        is_direct_http = is_direct_download_url(url)
        print(f"  HTTP Header Check: {is_direct_http}")
        
        # Test platform detection
        platform = get_platform_from_url(url)
        display_name = get_platform_display_name(platform)
        is_direct_platform = platform == 'direct_url'
        
        print(f"  Platform Detection: {platform} ({display_name})")
        print(f"  Final Result: {'✓ Direct URL' if is_direct_platform else '❌ Not Direct URL'}")
        print("-" * 70)

def test_direct_url_metadata():
    """Test metadata extraction for direct URLs"""
    print("\n=== Testing Direct URL Metadata Extraction ===")
    
    test_urls = [
        'https://sample-videos.com/zip/10/mp4/SampleVideo_720x480_1mb.mp4',
        'https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/BigBuckBunny.mp4'
    ]
    
    for url in test_urls:
        try:
            print(f"\nTesting: {url}")
            metadata = extract_platform_metadata(url)
            
            print(f"✓ Title: {metadata.get('title')}")
            print(f"✓ Description: {metadata.get('description')}")
            print(f"✓ Platform: {metadata.get('platform')}")
            print(f"✓ Tags: {metadata.get('tags')}")
            
        except Exception as e:
            print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_direct_url_detection()
    test_direct_url_metadata()
    print("\n✓ Direct URL testing completed")
