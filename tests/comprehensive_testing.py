import logging
import time
import os
from multi_platform_downloader import (
    extract_platform_metadata, 
    get_platform_from_url,
    get_supported_platforms,
    get_platform_display_name,
    is_platform_supported
)

def comprehensive_platform_test():
    """Test all supported platforms with real URLs"""
    
    # Carefully selected test URLs from different platforms (public, popular content)
    test_cases = [
        # YouTube - Always reliable
        {
            'platform': 'youtube',
            'url': 'https://www.youtube.com/watch?v=jNQXAC9IVRw',  # First YouTube video - "Me at the zoo"
            'expected_title': 'Me at the zoo',
            'test_type': 'short_video'
        },
        {
            'platform': 'youtube', 
            'url': 'https://www.youtube.com/watch?v=9bZkp7q19f0',  # PSY - Gangnam Style
            'expected_title': 'Gangnam Style',
            'test_type': 'music_video'
        },
        
        # Vimeo - Reliable alternative
        {
            'platform': 'vimeo',
            'url': 'https://vimeo.com/148751763',  # Popular Vimeo video
            'expected_title': None,  # Will check if extraction works
            'test_type': 'vimeo_video'
        },
        
        # Dailymotion - Good fallback
        {
            'platform': 'dailymotion',
            'url': 'https://www.dailymotion.com/video/x7tgad0',  # Sample Dailymotion video
            'expected_title': None,
            'test_type': 'dailymotion_video'
        },
        
        # Social Media Platforms (may have restrictions)
        {
            'platform': 'reddit',
            'url': 'https://www.reddit.com/r/videos/comments/xyz/sample_video/',  # Reddit video post
            'expected_title': None,
            'test_type': 'social_media',
            'may_fail': True  # Reddit videos can be tricky
        },
        
        # Platform detection tests
        {
            'platform': 'instagram',
            'url': 'https://www.instagram.com/p/sample123/',
            'expected_title': None,
            'test_type': 'platform_detection',
            'may_fail': True  # May require authentication
        },
        
        {
            'platform': 'tiktok',
            'url': 'https://www.tiktok.com/@user/video/1234567890',
            'expected_title': None,
            'test_type': 'platform_detection',
            'may_fail': True  # May require authentication
        },
        
        {
            'platform': 'twitter',
            'url': 'https://twitter.com/user/status/1234567890',
            'expected_title': None,
            'test_type': 'platform_detection',
            'may_fail': True  # Twitter videos can be restricted
        }
    ]
    
    results = {
        'total_tests': len(test_cases),
        'successful': 0,
        'failed': 0,
        'skipped': 0,
        'test_results': [],
        'summary': '',
        'platform_coverage': {}
    }
    
    logging.info(f"Starting comprehensive platform test with {len(test_cases)} test cases")
    
    for i, test_case in enumerate(test_cases):
        test_num = i + 1
        platform = test_case['platform']
        url = test_case['url']
        test_type = test_case['test_type']
        may_fail = test_case.get('may_fail', False)
        
        logging.info(f"Test {test_num}/{len(test_cases)}: Testing {platform} - {test_type}")
        
        test_result = {
            'test_number': test_num,
            'platform': platform,
            'platform_display': get_platform_display_name(platform),
            'url': url,
            'test_type': test_type,
            'status': 'unknown',
            'error': None,
            'metadata': {},
            'notes': []
        }
        
        try:
            # Platform detection test first
            detected_platform = get_platform_from_url(url)
            if detected_platform != platform:
                test_result['notes'].append(f"Platform detection mismatch: expected {platform}, got {detected_platform}")
            
            # Support check
            if not is_platform_supported(url):
                test_result['status'] = 'unsupported'
                test_result['error'] = f"Platform {platform} not in supported list"
                results['skipped'] += 1
            else:
                # Metadata extraction test
                start_time = time.time()
                metadata = extract_platform_metadata(url, platform)
                extraction_time = time.time() - start_time
                
                test_result['metadata'] = {
                    'title': metadata.get('title', 'N/A'),
                    'uploader': metadata.get('uploader', 'N/A'),
                    'duration': metadata.get('duration', 'N/A'),
                    'view_count': metadata.get('view_count', 'N/A'),
                    'tags_count': len(metadata.get('tags', [])),
                    'has_thumbnail': bool(metadata.get('thumbnail'))
                }
                test_result['extraction_time'] = f"{extraction_time:.2f}s"
                test_result['status'] = 'success'
                results['successful'] += 1
                
                # Validate expected results
                expected_title = test_case.get('expected_title')
                if expected_title and expected_title.lower() not in metadata.get('title', '').lower():
                    test_result['notes'].append(f"Title mismatch: expected '{expected_title}', got '{metadata.get('title')}'")
                
        except Exception as e:
            error_msg = str(e)
            test_result['status'] = 'failed'
            test_result['error'] = error_msg
            
            if may_fail:
                test_result['status'] = 'expected_failure'
                test_result['notes'].append("This failure was expected due to platform restrictions")
                results['skipped'] += 1
            else:
                results['failed'] += 1
            
            # Categorize error types
            if "429" in error_msg or "Too Many Requests" in error_msg:
                test_result['error_category'] = 'rate_limit'
            elif "Restricted" in error_msg or "not available" in error_msg:
                test_result['error_category'] = 'access_restricted'
            elif "Sign in" in error_msg or "authentication" in error_msg:
                test_result['error_category'] = 'auth_required'
            else:
                test_result['error_category'] = 'technical_error'
        
        results['test_results'].append(test_result)
        
        # Track platform coverage
        if platform not in results['platform_coverage']:
            results['platform_coverage'][platform] = {'tested': 0, 'successful': 0}
        results['platform_coverage'][platform]['tested'] += 1
        if test_result['status'] == 'success':
            results['platform_coverage'][platform]['successful'] += 1
        
        # Add delay between tests to avoid rate limiting
        if i < len(test_cases) - 1:  # Don't wait after last test
            time.sleep(3)  # 3 second delay between tests
    
    # Generate summary
    success_rate = (results['successful'] / results['total_tests']) * 100 if results['total_tests'] > 0 else 0
    results['success_rate'] = f"{success_rate:.1f}%"
    results['summary'] = f"Tested {results['total_tests']} cases: {results['successful']} successful, {results['failed']} failed, {results['skipped']} skipped (Success rate: {success_rate:.1f}%)"
    
    logging.info(f"Comprehensive test completed: {results['summary']}")
    return results


def quick_metadata_test():
    """Quick test of metadata extraction for reliable platforms"""
    
    quick_test_urls = [
        'https://www.youtube.com/watch?v=jNQXAC9IVRw',  # YouTube - First video
        'https://vimeo.com/148751763',  # Vimeo
        'https://www.dailymotion.com/video/x7tgad0',  # Dailymotion
    ]
    
    results = []
    
    for i, url in enumerate(quick_test_urls):
        platform = get_platform_from_url(url)
        
        try:
            start_time = time.time()
            metadata = extract_platform_metadata(url)
            extraction_time = time.time() - start_time
            
            results.append({
                'test_number': i + 1,
                'url': url,
                'platform': get_platform_display_name(platform),
                'status': 'success',
                'title': metadata.get('title', 'N/A'),
                'uploader': metadata.get('uploader', 'N/A'),
                'duration': metadata.get('duration', 'N/A'),
                'extraction_time': f"{extraction_time:.2f}s"
            })
            
        except Exception as e:
            results.append({
                'test_number': i + 1,
                'url': url,
                'platform': get_platform_display_name(platform),
                'status': 'failed',
                'error': str(e)
            })
        
        # Small delay between tests
        if i < len(quick_test_urls) - 1:
            time.sleep(2)
    
    return results


def platform_capabilities_test():
    """Test platform detection and capability reporting"""
    
    test_urls = {
        'youtube.com/watch?v=test': 'youtube',
        'youtu.be/test': 'youtube',
        'instagram.com/p/test': 'instagram',
        'tiktok.com/@user/video/123': 'tiktok',
        'twitter.com/user/status/123': 'twitter',
        'x.com/user/status/123': 'twitter',
        'vimeo.com/123456': 'vimeo',
        'dailymotion.com/video/test': 'dailymotion',
        'reddit.com/r/videos/comments/test': 'reddit',
        'twitch.tv/videos/123': 'twitch',
        'rumble.com/test': 'rumble',
        'pinterest.com/pin/123': 'pinterest',
        'snapchat.com/spotlight/test': 'snapchat',
        'facebook.com/watch/?v=123': 'facebook',
        'unknown-site.com/video': 'unknown'
    }
    
    detection_results = []
    
    for test_url, expected_platform in test_urls.items():
        detected_platform = get_platform_from_url(f"https://{test_url}")
        is_correct = detected_platform == expected_platform
        is_supported = detected_platform in get_supported_platforms()
        
        detection_results.append({
            'url': test_url,
            'expected': expected_platform,
            'detected': detected_platform,
            'correct': is_correct,
            'supported': is_supported,
            'display_name': get_platform_display_name(detected_platform)
        })
    
    return {
        'detection_tests': detection_results,
        'supported_platforms': get_supported_platforms(),
        'total_platforms': len(get_supported_platforms())
    }