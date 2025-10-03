
#!/usr/bin/env python3

import sys
import time
import logging
from multi_platform_downloader import (
    extract_platform_metadata, 
    get_platform_from_url,
    get_supported_platforms,
    is_platform_supported
)

# Configure logging
logging.basicConfig(level=logging.INFO)

def test_all_platforms():
    """Test all supported platforms with sample URLs"""
    
    test_urls = {
        'youtube': [
            'https://www.youtube.com/watch?v=dQw4w9WgXcQ',
            'https://youtu.be/dQw4w9WgXcQ'
        ],
        'instagram': [
            'https://www.instagram.com/p/DNcjuqQo-OYvClSgyCuCrhrqN9QwYDcycD0Jbk0/',
            'https://www.instagram.com/reel/DOQzHA0DcrL'
        ],
        'facebook': [
            'https://www.facebook.com/watch/?v=755703039304226',
            'https://www.facebook.com/100001575291151/videos/1652817099353630/?_so__=disco'
        ],
        'twitter': [
            'https://x.com/ShriRamTeerth/status/1963904565633286339',
            'https://x.com/ShriRamTeerth/status/1957672012417212612'
        ],
        'tiktok': [
            'https://www.tiktok.com/@user/video/1234567890',
            'https://vm.tiktok.com/sample123/'
        ],
        'vimeo': [
            'https://vimeo.com/groups/114/videos/1017406920',
            'https://vimeo.com/1093837607?fl=wc'
        ],
        'dailymotion': [
            'https://www.dailymotion.com/video/x7vnx7w',
            'https://www.dailymotion.com/video/x6wz9mk'
        ],
        'reddit': [
            'https://www.reddit.com/r/videos/comments/abv123/sample_video_post/',
            'https://old.reddit.com/r/videos/comments/abv123/sample_video_post/'
        ],
        'twitch': [
            'https://www.twitch.tv/videos/987654321',
            'https://clips.twitch.tv/AwesomeClip123'
        ],
        'rumble': [
            'https://rumble.com/v6xapxy-tofags3ep01-eng-sub-4k',
            'https://rumble.com/embed/v6wbuhu/?pub=3sg0xe'
        ],
        'pinterest': [
            'https://www.pinterest.com/pin/987654321/',
            'https://pin.it/sample123'
        ],
        'snapchat': [
            'https://www.snapchat.com/spotlight/W7_sample',
            'https://story.snapchat.com/s/sample'
        ]
    }
    
    results = {
        'platform_detection': {},
        'metadata_extraction': {},
        'successful_platforms': [],
        'failed_platforms': [],
        'total_tests': 0,
        'successful_tests': 0,
        'failed_tests': 0
    }
    
    print("🧪 COMPREHENSIVE PLATFORM TESTING")
    print("=" * 50)
    
    for platform, urls in test_urls.items():
        print(f"\n🔍 Testing {platform.upper()}:")
        results['platform_detection'][platform] = []
        results['metadata_extraction'][platform] = []
        
        for url in urls:
            results['total_tests'] += 1
            
            # Test 1: Platform Detection
            detected_platform = get_platform_from_url(url)
            detection_result = {
                'url': url,
                'expected': platform,
                'detected': detected_platform,
                'correct': detected_platform == platform,
                'supported': is_platform_supported(url)
            }
            results['platform_detection'][platform].append(detection_result)
            
            if detection_result['correct']:
                print(f"  ✅ Detection: {url[:50]}... -> {detected_platform}")
            else:
                print(f"  ❌ Detection: {url[:50]}... -> Expected: {platform}, Got: {detected_platform}")
            
            # Test 2: Metadata Extraction (only for correctly detected platforms)
            if detection_result['correct'] and detection_result['supported']:
                try:
                    print(f"  🔄 Extracting metadata...")
                    start_time = time.time()
                    
                    metadata = extract_platform_metadata(url, platform)
                    extraction_time = time.time() - start_time
                    
                    metadata_result = {
                        'url': url,
                        'status': 'success',
                        'extraction_time': f"{extraction_time:.2f}s",
                        'title': metadata.get('title', 'N/A')[:50] + '...' if len(metadata.get('title', '')) > 50 else metadata.get('title', 'N/A'),
                        'uploader': metadata.get('uploader', 'N/A'),
                        'duration': metadata.get('duration', 'N/A'),
                        'view_count': metadata.get('view_count', 'N/A'),
                        'tags_count': len(metadata.get('tags', [])),
                        'has_thumbnail': bool(metadata.get('thumbnail'))
                    }
                    
                    results['metadata_extraction'][platform].append(metadata_result)
                    results['successful_tests'] += 1
                    
                    print(f"  ✅ Metadata: {metadata_result['title']}")
                    print(f"     ⏱️  Time: {metadata_result['extraction_time']}")
                    print(f"     👤 Uploader: {metadata_result['uploader']}")
                    print(f"     ⏰ Duration: {metadata_result['duration']}")
                    print(f"     👁️  Views: {metadata_result['view_count']}")
                    
                except Exception as e:
                    error_msg = str(e)[:100]
                    metadata_result = {
                        'url': url,
                        'status': 'failed',
                        'error': error_msg,
                        'error_type': type(e).__name__
                    }
                    
                    results['metadata_extraction'][platform].append(metadata_result)
                    results['failed_tests'] += 1
                    
                    print(f"  ❌ Metadata failed: {error_msg}")
                    
                    # Wait a bit to avoid rate limiting
                    time.sleep(1)
            else:
                print(f"  ⏭️  Skipping metadata extraction (detection failed or unsupported)")
                results['failed_tests'] += 1
    
    # Generate Summary
    print("\n" + "=" * 50)
    print("📊 TEST SUMMARY")
    print("=" * 50)
    print(f"Total Tests: {results['total_tests']}")
    print(f"Successful: {results['successful_tests']}")
    print(f"Failed: {results['failed_tests']}")
    print(f"Success Rate: {(results['successful_tests']/results['total_tests']*100):.1f}%")
    
    # Platform-wise summary
    print("\n🏆 PLATFORM SUCCESS RATES:")
    for platform in test_urls.keys():
        platform_tests = len(test_urls[platform])
        platform_successes = len([r for r in results['metadata_extraction'].get(platform, []) if r.get('status') == 'success'])
        success_rate = (platform_successes / platform_tests * 100) if platform_tests > 0 else 0
        
        if success_rate > 50:
            results['successful_platforms'].append(platform)
            print(f"  ✅ {platform.capitalize()}: {platform_successes}/{platform_tests} ({success_rate:.1f}%)")
        else:
            results['failed_platforms'].append(platform)
            print(f"  ❌ {platform.capitalize()}: {platform_successes}/{platform_tests} ({success_rate:.1f}%)")
    
    # Identify issues
    print("\n🔧 ISSUES DETECTED:")
    common_errors = {}
    for platform_results in results['metadata_extraction'].values():
        for result in platform_results:
            if result.get('status') == 'failed':
                error_type = result.get('error_type', 'Unknown')
                if error_type not in common_errors:
                    common_errors[error_type] = []
                common_errors[error_type].append(result.get('error', ''))
    
    for error_type, errors in common_errors.items():
        print(f"  🐛 {error_type}: {len(errors)} occurrences")
        if errors:
            print(f"     Sample: {errors[0][:100]}...")
    
    return results

if __name__ == "__main__":
    try:
        results = test_all_platforms()
        
        # Save results to file
        import json
        with open('platform_test_results.json', 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        
        print(f"\n💾 Results saved to platform_test_results.json")
        
    except KeyboardInterrupt:
        print("\n⏹️  Testing stopped by user")
    except Exception as e:
        print(f"\n💥 Testing failed: {e}")
        sys.exit(1)
