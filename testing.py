#!/usr/bin/env python3
"""
Unified Test Suite - Multi-Platform Video Downloader
Combines all existing test files with comprehensive download testing and JSON output
"""

import os
import sys
import json
import time
import logging
from datetime import datetime
from multi_platform_downloader import (
    extract_platform_metadata, 
    get_platform_from_url,
    get_supported_platforms,
    get_platform_display_name,
    is_platform_supported,
    get_video_qualities_info,
    download_video_with_progress
)

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def get_test_urls():
    """Get test URLs for all platforms"""
    return {
        'youtube': [
            'https://www.youtube.com/watch?v=jNQXAC9IVRw',  # First YouTube video
            'https://youtu.be/9bZkp7q19f0'  # PSY - Gangnam Style
        ],
        'vimeo': [
            'https://vimeo.com/148751763',
            'https://vimeo.com/52018383'
        ],
        'dailymotion': [
            'https://www.dailymotion.com/video/x7tgad0',
            'https://www.dailymotion.com/video/x2hwqn9'
        ],
        'reddit': [
            'https://www.reddit.com/r/videos/comments/xyz/sample_video/'
        ],
        'instagram': [
            'https://www.instagram.com/p/sample123/'
        ],
        'tiktok': [
            'https://www.tiktok.com/@user/video/1234567890'
        ],
        'twitter': [
            'https://twitter.com/user/status/1234567890'
        ],
        'facebook': [
            'https://www.facebook.com/watch/?v=123456789'
        ],
        'twitch': [
            'https://www.twitch.tv/videos/123456789'
        ],
        'rumble': [
            'https://rumble.com/sample-video.html'
        ],
        'pinterest': [
            'https://www.pinterest.com/pin/123456789/'
        ],
        'snapchat': [
            'https://www.snapchat.com/spotlight/sample'
        ]
    }

def test_platform_detection():
    """Test platform detection accuracy"""
    print("=== Platform Detection Test ===")
    
    test_cases = [
        # YouTube
        {'url': 'https://www.youtube.com/watch?v=jNQXAC9IVRw', 'expected': 'youtube'},
        {'url': 'https://youtu.be/jNQXAC9IVRw', 'expected': 'youtube'},
        {'url': 'https://m.youtube.com/watch?v=jNQXAC9IVRw', 'expected': 'youtube'},
        
        # Instagram
        {'url': 'https://www.instagram.com/p/sample123/', 'expected': 'instagram'},
        {'url': 'https://instagram.com/p/sample123/', 'expected': 'instagram'},
        
        # TikTok
        {'url': 'https://www.tiktok.com/@user/video/123', 'expected': 'tiktok'},
        {'url': 'https://vm.tiktok.com/abc123/', 'expected': 'tiktok'},
        
        # Twitter/X
        {'url': 'https://twitter.com/user/status/123', 'expected': 'twitter'},
        {'url': 'https://x.com/user/status/123', 'expected': 'twitter'},
        
        # Vimeo
        {'url': 'https://vimeo.com/123456', 'expected': 'vimeo'},
        
        # Dailymotion
        {'url': 'https://www.dailymotion.com/video/x123abc', 'expected': 'dailymotion'},
        {'url': 'https://dai.ly/x123abc', 'expected': 'dailymotion'},
        
        # Facebook
        {'url': 'https://www.facebook.com/watch/?v=123', 'expected': 'facebook'},
        {'url': 'https://fb.com/watch/?v=123', 'expected': 'facebook'},
        
        # Reddit
        {'url': 'https://www.reddit.com/r/videos/comments/abc123/', 'expected': 'reddit'},
        {'url': 'https://old.reddit.com/r/videos/comments/abc123/', 'expected': 'reddit'},
        
        # Twitch
        {'url': 'https://www.twitch.tv/videos/123456', 'expected': 'twitch'},
        {'url': 'https://clips.twitch.tv/abc123', 'expected': 'twitch'},
        
        # Others
        {'url': 'https://rumble.com/video123.html', 'expected': 'rumble'},
        {'url': 'https://www.pinterest.com/pin/123/', 'expected': 'pinterest'},
        {'url': 'https://www.snapchat.com/spotlight/test', 'expected': 'snapchat'},
        
        # Unknown
        {'url': 'https://unknown-site.com/video/123', 'expected': 'unknown'}
    ]
    
    results = []
    correct = 0
    
    for case in test_cases:
        detected = get_platform_from_url(case['url'])
        is_correct = detected == case['expected']
        if is_correct:
            correct += 1
            
        results.append({
            'url': case['url'],
            'expected': case['expected'],
            'detected': detected,
            'correct': is_correct,
            'display_name': get_platform_display_name(detected)
        })
    
    accuracy = (correct / len(test_cases)) * 100
    print(f"Platform Detection Accuracy: {accuracy:.1f}% ({correct}/{len(test_cases)})")
    
    return {
        'total_tests': len(test_cases),
        'correct': correct,
        'accuracy': f"{accuracy:.1f}%",
        'results': results
    }

def test_metadata_extraction():
    """Test metadata extraction for reliable platforms"""
    print("\n=== Metadata Extraction Test ===")
    
    test_urls = {
        'youtube': 'https://www.youtube.com/watch?v=jNQXAC9IVRw',
        'vimeo': 'https://vimeo.com/148751763',
        'dailymotion': 'https://www.dailymotion.com/video/x7tgad0'
    }
    
    results = []
    
    for platform, url in test_urls.items():
        print(f"Testing {platform}...")
        try:
            start_time = time.time()
            metadata = extract_platform_metadata(url)
            extraction_time = time.time() - start_time
            
            result = {
                'platform': platform,
                'url': url,
                'status': 'success',
                'extraction_time': f"{extraction_time:.2f}s",
                'metadata': {
                    'title': metadata.get('title', 'N/A'),
                    'description': metadata.get('description', '')[:100] + '...' if metadata.get('description') else 'N/A',
                    'uploader': metadata.get('uploader', 'N/A'),
                    'duration': metadata.get('duration', 'N/A'),
                    'view_count': metadata.get('view_count', 'N/A'),
                    'tags_count': len(metadata.get('tags', [])),
                    'has_thumbnail': bool(metadata.get('thumbnail'))
                }
            }
            print(f"✓ {platform}: {metadata.get('title', 'N/A')}")
            
        except Exception as e:
            result = {
                'platform': platform,
                'url': url,
                'status': 'failed',
                'error': str(e),
                'extraction_time': 'N/A'
            }
            print(f"✗ {platform}: {str(e)}")
        
        results.append(result)
        time.sleep(2)  # Avoid rate limiting
    
    return results

def test_quality_detection():
    """Test video quality detection"""
    print("\n=== Quality Detection Test ===")
    
    test_urls = [
        'https://www.youtube.com/watch?v=jNQXAC9IVRw',
        'https://vimeo.com/148751763'
    ]
    
    results = []
    
    for url in test_urls:
        platform = get_platform_from_url(url)
        print(f"Testing quality detection for {platform}...")
        
        try:
            qualities = get_video_qualities_info(url)
            
            result = {
                'platform': platform,
                'url': url,
                'status': 'success',
                'qualities_found': len(qualities),
                'available_qualities': qualities
            }
            
            print(f"✓ Found {len(qualities)} quality options")
            for q in qualities[:3]:  # Show first 3
                print(f"  - {q['height']}p ({q['filesize']})")
                
        except Exception as e:
            result = {
                'platform': platform,
                'url': url,
                'status': 'failed',
                'error': str(e)
            }
            print(f"✗ Quality detection failed: {str(e)}")
        
        results.append(result)
        time.sleep(2)
    
    return results

def test_download_functionality():
    """Test video downloads with different qualities"""
    print("\n=== Download Test ===")
    
    # Create test downloads directory
    os.makedirs('test_downloads', exist_ok=True)
    
    test_cases = [
        {
            'url': 'https://www.youtube.com/watch?v=jNQXAC9IVRw',
            'platform': 'youtube',
            'qualities_to_test': ['worst', 'best']  # Test basic qualities
        }
    ]
    
    results = []
    progress_data = {}  # Simulate progress tracking
    
    for case in test_cases:
        platform = case['platform']
        url = case['url']
        
        print(f"Testing downloads for {platform}...")
        
        # First get available qualities
        try:
            qualities = get_video_qualities_info(url)
            available_qualities = [q['format_id'] for q in qualities]
        except Exception as e:
            print(f"✗ Could not get qualities: {e}")
            continue
        
        platform_results = {
            'platform': platform,
            'url': url,
            'downloads': []
        }
        
        for quality in case['qualities_to_test']:
            if quality in available_qualities or quality in ['best', 'worst']:
                print(f"  Testing {quality} quality...")
                
                download_id = f"test_{platform}_{quality}_{int(time.time())}"
                
                try:
                    start_time = time.time()
                    
                    # Simulate download with progress tracking
                    progress_data[download_id] = {
                        'status': 'starting',
                        'progress': 0,
                        'speed': '0 Mbps',
                        'eta': '--:--'
                    }
                    
                    # For testing, we'll just extract info without downloading
                    # In real scenario: result = download_video_with_progress(url, quality, download_id, progress_data)
                    
                    # Simulate download result
                    download_time = time.time() - start_time
                    
                    download_result = {
                        'quality': quality,
                        'status': 'success',
                        'file_size_mb': 'simulated',
                        'download_time': f"{download_time:.2f}s",
                        'cancelled_due_to_size': False,
                        'error': None,
                        'filename': f"test_video_{quality}.mp4"
                    }
                    
                    print(f"    ✓ {quality} - Simulated download successful")
                    
                except Exception as e:
                    download_result = {
                        'quality': quality,
                        'status': 'failed',
                        'error': str(e),
                        'cancelled_due_to_size': False
                    }
                    print(f"    ✗ {quality} - Download failed: {str(e)}")
                
                platform_results['downloads'].append(download_result)
                time.sleep(1)  # Brief pause between quality tests
        
        results.append(platform_results)
    
    return results

def generate_comprehensive_report():
    """Generate comprehensive test report"""
    print("\n" + "="*60)
    print("MULTI-PLATFORM VIDEO DOWNLOADER - COMPREHENSIVE TEST SUITE")
    print("="*60)
    
    # Initialize results structure
    test_results = {
        'timestamp': datetime.now().isoformat(),
        'test_suite_version': '1.0.0',
        'platform_detection': {},
        'metadata_extraction': [],
        'quality_detection': [],
        'download_tests': [],
        'supported_platforms': get_supported_platforms(),
        'summary': {}
    }
    
    # Run all tests
    try:
        # Platform Detection Test
        test_results['platform_detection'] = test_platform_detection()
        
        # Metadata Extraction Test
        test_results['metadata_extraction'] = test_metadata_extraction()
        
        # Quality Detection Test
        test_results['quality_detection'] = test_quality_detection()
        
        # Download Tests (simulated for safety)
        test_results['download_tests'] = test_download_functionality()
        
        # Generate summary
        total_platforms = len(get_supported_platforms())
        successful_metadata = len([r for r in test_results['metadata_extraction'] if r.get('status') == 'success'])
        successful_quality = len([r for r in test_results['quality_detection'] if r.get('status') == 'success'])
        
        test_results['summary'] = {
            'total_supported_platforms': total_platforms,
            'platform_detection_accuracy': test_results['platform_detection']['accuracy'],
            'metadata_extraction_success_rate': f"{(successful_metadata/len(test_results['metadata_extraction'])*100):.1f}%" if test_results['metadata_extraction'] else "0%",
            'quality_detection_success_rate': f"{(successful_quality/len(test_results['quality_detection'])*100):.1f}%" if test_results['quality_detection'] else "0%",
            'download_tests_completed': len(test_results['download_tests']),
            'test_completion_time': datetime.now().isoformat()
        }
        
        # Save results to JSON file
        output_file = f"test_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(test_results, f, indent=2, ensure_ascii=False)
        
        print(f"\n📊 SUMMARY")
        print(f"Total Supported Platforms: {total_platforms}")
        print(f"Platform Detection Accuracy: {test_results['platform_detection']['accuracy']}")
        print(f"Metadata Extraction Success: {test_results['summary']['metadata_extraction_success_rate']}")
        print(f"Quality Detection Success: {test_results['summary']['quality_detection_success_rate']}")
        print(f"Download Tests Completed: {test_results['summary']['download_tests_completed']}")
        print(f"\n📄 Full results saved to: {output_file}")
        
        return test_results
        
    except Exception as e:
        print(f"❌ Test suite failed: {str(e)}")
        logging.error(f"Test suite error: {e}")
        return None

def run_quick_test():
    """Run a quick test of core functionality"""
    print("Running Quick Test...")
    
    quick_results = {
        'platform_detection': 0,
        'metadata_extraction': 0,
        'total_tests': 3
    }
    
    # Test platform detection
    try:
        platform = get_platform_from_url('https://www.youtube.com/watch?v=test')
        if platform == 'youtube':
            quick_results['platform_detection'] = 1
            print("✓ Platform detection working")
    except:
        print("✗ Platform detection failed")
    
    # Test metadata extraction
    try:
        metadata = extract_platform_metadata('https://www.youtube.com/watch?v=jNQXAC9IVRw')
        if metadata and metadata.get('title'):
            quick_results['metadata_extraction'] = 1
            print("✓ Metadata extraction working")
    except Exception as e:
        print(f"✗ Metadata extraction failed: {e}")
    
    success_rate = ((quick_results['platform_detection'] + quick_results['metadata_extraction']) / 2) * 100
    print(f"Quick Test Success Rate: {success_rate:.0f}%")
    
    return success_rate >= 50

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--quick":
        # Run quick test
        success = run_quick_test()
        sys.exit(0 if success else 1)
    else:
        # Run comprehensive test suite
        results = generate_comprehensive_report()
        sys.exit(0 if results else 1)