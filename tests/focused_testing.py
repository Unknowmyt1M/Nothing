import logging
import time
from multi_platform_downloader import (
    extract_platform_metadata, 
    get_platform_from_url,
    get_platform_display_name
)

def test_reliable_platforms():
    """Test platforms that are known to work reliably"""
    
    # Curated list of working, publicly accessible videos
    reliable_test_cases = [
        {
            'name': 'YouTube - First Video',
            'url': 'https://www.youtube.com/watch?v=jNQXAC9IVRw',
            'expected_platform': 'youtube',
            'should_work': True
        },
        {
            'name': 'YouTube - Popular Music',
            'url': 'https://www.youtube.com/watch?v=9bZkp7q19f0',
            'expected_platform': 'youtube', 
            'should_work': True
        },
        {
            'name': 'Dailymotion - Demo Video',
            'url': 'https://www.dailymotion.com/video/x7tgad0',
            'expected_platform': 'dailymotion',
            'should_work': True
        },
        {
            'name': 'YouTube - Short Educational',
            'url': 'https://www.youtube.com/watch?v=hFZFjoX2cGg',
            'expected_platform': 'youtube',
            'should_work': True
        },
        {
            'name': 'Instagram - Test Detection (may fail)',
            'url': 'https://www.instagram.com/p/DNE4s7zpy58/',
            'expected_platform': 'instagram',
            'should_work': False  # Expected to fail without proper cookies
        },
        {
            'name': 'TikTok - Test Detection (may fail)',
            'url': 'https://www.tiktok.com/@user/video/1234567890',
            'expected_platform': 'tiktok',
            'should_work': False  # Expected to fail without proper access
        }
    ]
    
    results = {
        'test_name': 'Reliable Platforms Test',
        'total_tests': len(reliable_test_cases),
        'successful': 0,
        'failed': 0,
        'expected_failures': 0,
        'test_results': [],
        'summary': ''
    }
    
    logging.info(f"Starting reliable platforms test with {len(reliable_test_cases)} test cases")
    
    for i, test_case in enumerate(reliable_test_cases):
        test_num = i + 1
        test_name = test_case['name']
        url = test_case['url']
        expected_platform = test_case['expected_platform']
        should_work = test_case['should_work']
        
        logging.info(f"Test {test_num}/{len(reliable_test_cases)}: {test_name}")
        
        test_result = {
            'test_number': test_num,
            'name': test_name,
            'url': url,
            'expected_platform': expected_platform,
            'should_work': should_work,
            'status': 'unknown',
            'platform_detected': None,
            'metadata': {},
            'error': None,
            'notes': []
        }
        
        try:
            # Platform detection test
            detected_platform = get_platform_from_url(url)
            test_result['platform_detected'] = detected_platform
            
            if detected_platform != expected_platform:
                test_result['notes'].append(f"Platform detection issue: expected {expected_platform}, got {detected_platform}")
            
            # Metadata extraction test
            start_time = time.time()
            metadata = extract_platform_metadata(url, detected_platform)
            extraction_time = time.time() - start_time
            
            # Success!
            test_result['status'] = 'success'
            test_result['metadata'] = {
                'title': metadata.get('title', 'N/A'),
                'uploader': metadata.get('uploader', 'N/A'),
                'duration': metadata.get('duration', 'N/A'),
                'view_count': metadata.get('view_count', 'N/A'),
                'tags_count': len(metadata.get('tags', [])),
                'extraction_time': f"{extraction_time:.2f}s"
            }
            
            if should_work:
                results['successful'] += 1
            else:
                test_result['notes'].append("Unexpected success - this was expected to fail!")
                results['successful'] += 1
                
        except Exception as e:
            error_msg = str(e)
            test_result['status'] = 'failed'
            test_result['error'] = error_msg
            
            if not should_work:
                test_result['status'] = 'expected_failure'
                test_result['notes'].append("Expected failure due to platform restrictions")
                results['expected_failures'] += 1
            else:
                results['failed'] += 1
            
            # Categorize error
            if "429" in error_msg or "Too Many Requests" in error_msg:
                test_result['error_category'] = 'rate_limit'
            elif "authentication" in error_msg.lower() or "login" in error_msg.lower():
                test_result['error_category'] = 'auth_required'
            elif "empty media response" in error_msg.lower() or "not accessible" in error_msg.lower():
                test_result['error_category'] = 'access_restricted'
            else:
                test_result['error_category'] = 'technical_error'
        
        results['test_results'].append(test_result)
        
        # Small delay to avoid overwhelming servers
        if i < len(reliable_test_cases) - 1:
            time.sleep(1)
    
    # Generate summary
    working_rate = (results['successful'] / results['total_tests']) * 100 if results['total_tests'] > 0 else 0
    results['working_rate'] = f"{working_rate:.1f}%"
    results['summary'] = f"Tested {results['total_tests']} cases: {results['successful']} successful, {results['failed']} failed, {results['expected_failures']} expected failures (Working rate: {working_rate:.1f}%)"
    
    logging.info(f"Reliable platforms test completed: {results['summary']}")
    return results


def test_platform_detection_accuracy():
    """Test platform detection with various URL formats"""
    
    detection_test_cases = [
        # YouTube variations
        {'url': 'https://www.youtube.com/watch?v=jNQXAC9IVRw', 'expected': 'youtube'},
        {'url': 'https://youtu.be/jNQXAC9IVRw', 'expected': 'youtube'},
        {'url': 'https://m.youtube.com/watch?v=jNQXAC9IVRw', 'expected': 'youtube'},
        
        # Social media
        {'url': 'https://www.instagram.com/p/sample123/', 'expected': 'instagram'},
        {'url': 'https://www.tiktok.com/@user/video/123', 'expected': 'tiktok'},
        {'url': 'https://twitter.com/user/status/123', 'expected': 'twitter'},
        {'url': 'https://x.com/user/status/123', 'expected': 'twitter'},
        {'url': 'https://www.facebook.com/watch/?v=123', 'expected': 'facebook'},
        
        # Other platforms  
        {'url': 'https://vimeo.com/123456', 'expected': 'vimeo'},
        {'url': 'https://www.dailymotion.com/video/test', 'expected': 'dailymotion'},
        {'url': 'https://www.reddit.com/r/videos/comments/abc/sample/', 'expected': 'reddit'},
        {'url': 'https://www.twitch.tv/videos/123', 'expected': 'twitch'},
        {'url': 'https://rumble.com/video-test.html', 'expected': 'rumble'},
        {'url': 'https://www.pinterest.com/pin/123456/', 'expected': 'pinterest'},
        {'url': 'https://www.snapchat.com/spotlight/W7_EDlXWTBiXAEEniNoMPwAAYbGkY4HlNoKGH', 'expected': 'snapchat'},
    ]
    
    results = {
        'total_tests': len(detection_test_cases),
        'correct': 0,
        'incorrect': 0,
        'detection_results': []
    }
    
    for test_case in detection_test_cases:
        url = test_case['url']
        expected = test_case['expected']
        
        detected = get_platform_from_url(url)
        is_correct = detected == expected
        
        if is_correct:
            results['correct'] += 1
        else:
            results['incorrect'] += 1
        
        results['detection_results'].append({
            'url': url,
            'expected': expected,
            'detected': detected,
            'correct': is_correct,
            'display_name': get_platform_display_name(detected)
        })
    
    accuracy = (results['correct'] / results['total_tests']) * 100 if results['total_tests'] > 0 else 0
    results['accuracy'] = f"{accuracy:.1f}%"
    results['summary'] = f"Detection accuracy: {results['correct']}/{results['total_tests']} correct ({accuracy:.1f}%)"
    
    return results