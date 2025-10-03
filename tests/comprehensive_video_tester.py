
#!/usr/bin/env python3
"""
Comprehensive Video Testing Script
Merges all test scripts and adds video downloading tests with quality management
"""

import os
import sys
import json
import time
import logging
import requests
import subprocess
from urllib.parse import urlparse
import shutil

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Import multi-platform downloader functions
from multi_platform_downloader import (
    extract_platform_metadata, 
    get_platform_from_url,
    get_supported_platforms,
    get_platform_display_name,
    is_platform_supported,
    download_from_platform,
    get_platform_config
)

class ComprehensiveVideoTester:
    def __init__(self):
        self.test_results = {
            'platform_detection': {},
            'metadata_extraction': {},
            'video_downloads': {},
            'quality_tests': {},
            'file_size_tests': {},
            'total_tests': 0,
            'successful_tests': 0,
            'failed_tests': 0,
            'download_stats': {}
        }
        
        # Create test directories
        self.test_dir = 'test_downloads'
        self.create_test_directories()
        
        # Quality settings for testing
        self.quality_levels = ['144p', '240p', '360p', '480p', '720p', '1080p', '1440p', '2160p']
        self.max_file_size_mb = 300  # Cancel downloads if file size > 300MB
        
    def create_test_directories(self):
        """Create necessary test directories"""
        try:
            os.makedirs(self.test_dir, exist_ok=True)
            os.makedirs('test_results', exist_ok=True)
            logging.info(f"Created test directories: {self.test_dir}, test_results")
        except Exception as e:
            logging.error(f"Failed to create test directories: {e}")

    def cleanup_downloaded_file(self, file_path):
        """Clean up downloaded file and related files"""
        try:
            if file_path and os.path.exists(file_path):
                os.remove(file_path)
                logging.info(f"Cleaned up: {file_path}")
                
                # Clean up related files
                for ext in ['.info.json', '.description', '.part']:
                    related_file = file_path + ext
                    if os.path.exists(related_file):
                        os.remove(related_file)
                        
        except Exception as e:
            logging.warning(f"Failed to cleanup {file_path}: {e}")

    def get_file_size_mb(self, file_path):
        """Get file size in MB"""
        try:
            if os.path.exists(file_path):
                size_bytes = os.path.getsize(file_path)
                return round(size_bytes / (1024 * 1024), 2)
        except Exception:
            pass
        return 0

    def format_bytes(self, bytes_value):
        """Format bytes to human readable string"""
        if not bytes_value:
            return "0 B"
        
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if bytes_value < 1024.0:
                return f"{bytes_value:.1f} {unit}"
            bytes_value /= 1024.0
        return f"{bytes_value:.1f} PB"

    def test_platform_detection(self):
        """Test platform detection with various URL formats"""
        logging.info("=== TESTING PLATFORM DETECTION ===")
        
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
            {'url': 'https://www.snapchat.com/spotlight/test', 'expected': 'snapchat'},
            
            # Direct URLs
            {'url': 'https://example.com/video.mp4', 'expected': 'direct_url'},
            {'url': 'https://sample-videos.com/zip/10/mp4/SampleVideo_720x480_1mb.mp4', 'expected': 'direct_url'},
        ]
        
        detection_results = []
        correct_count = 0
        
        for test_case in detection_test_cases:
            url = test_case['url']
            expected = test_case['expected']
            
            detected = get_platform_from_url(url)
            is_correct = detected == expected
            
            if is_correct:
                correct_count += 1
            
            detection_results.append({
                'url': url,
                'expected': expected,
                'detected': detected,
                'correct': is_correct,
                'display_name': get_platform_display_name(detected)
            })
            
            status = "✓" if is_correct else "❌"
            logging.info(f"{status} {url[:50]}... -> Expected: {expected}, Got: {detected}")
        
        accuracy = (correct_count / len(detection_test_cases)) * 100
        logging.info(f"Platform Detection Accuracy: {correct_count}/{len(detection_test_cases)} ({accuracy:.1f}%)")
        
        self.test_results['platform_detection'] = {
            'results': detection_results,
            'accuracy': f"{accuracy:.1f}%",
            'correct': correct_count,
            'total': len(detection_test_cases)
        }

    def test_metadata_extraction(self):
        """Test metadata extraction for reliable platforms"""
        logging.info("\n=== TESTING METADATA EXTRACTION ===")
        
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
                'name': 'Vimeo - Sample Video',
                'url': 'https://vimeo.com/148751763',
                'expected_platform': 'vimeo',
                'should_work': False  # May fail without proper cookies
            },
            {
                'name': 'Instagram - Test Detection',
                'url': 'https://www.instagram.com/p/DNE4s7zpy58/',
                'expected_platform': 'instagram',
                'should_work': False  # Expected to fail without proper cookies
            },
            {
                'name': 'Rumble - Sample Video',
                'url': 'https://rumble.com/v6xapxy-sample-video.html',
                'expected_platform': 'rumble',
                'should_work': True
            }
        ]
        
        metadata_results = []
        successful_count = 0
        
        for test_case in reliable_test_cases:
            test_name = test_case['name']
            url = test_case['url']
            expected_platform = test_case['expected_platform']
            should_work = test_case['should_work']
            
            logging.info(f"Testing: {test_name}")
            
            test_result = {
                'name': test_name,
                'url': url,
                'expected_platform': expected_platform,
                'should_work': should_work,
                'status': 'unknown',
                'platform_detected': None,
                'metadata': {},
                'error': None
            }
            
            try:
                # Platform detection test
                detected_platform = get_platform_from_url(url)
                test_result['platform_detected'] = detected_platform
                
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
                    'extraction_time': f"{extraction_time:.2f}s"
                }
                
                successful_count += 1
                logging.info(f"✓ Success: {metadata.get('title', 'N/A')[:50]}")
                
            except Exception as e:
                error_msg = str(e)
                test_result['status'] = 'failed' if should_work else 'expected_failure'
                test_result['error'] = error_msg
                
                status = "❌" if should_work else "⚠️"
                logging.info(f"{status} Failed: {error_msg[:100]}")
            
            metadata_results.append(test_result)
            time.sleep(1)  # Avoid rate limiting
        
        success_rate = (successful_count / len(reliable_test_cases)) * 100
        logging.info(f"Metadata Extraction Success Rate: {successful_count}/{len(reliable_test_cases)} ({success_rate:.1f}%)")
        
        self.test_results['metadata_extraction'] = {
            'results': metadata_results,
            'success_rate': f"{success_rate:.1f}%",
            'successful': successful_count,
            'total': len(reliable_test_cases)
        }

    def test_video_downloading_with_quality(self):
        """Test video downloading with different quality levels"""
        logging.info("\n=== TESTING VIDEO DOWNLOADING WITH QUALITY LEVELS ===")
        
        # Test videos for different platforms (2 videos per platform)
        download_test_videos = {
            'youtube': [
                'https://www.youtube.com/watch?v=jNQXAC9IVRw',  # Me at the zoo (short)
                'https://www.youtube.com/watch?v=hFZFjoX2cGg',  # Educational content (short)
            ],
            'dailymotion': [
                'https://www.dailymotion.com/video/x7tgad0',     # Demo video
                'https://www.dailymotion.com/video/x6wz9mk',     # Another demo
            ],
            'rumble': [
                'https://rumble.com/v6xapxy-sample-video.html',  # Sample video
                'https://rumble.com/embed/v6wbuhu/?pub=3sg0xe',  # Embedded video
            ]
        }
        
        download_results = {}
        
        for platform, urls in download_test_videos.items():
            logging.info(f"\n--- Testing {platform.upper()} Downloads ---")
            platform_results = []
            
            for i, url in enumerate(urls):
                video_num = i + 1
                logging.info(f"Testing Video {video_num}: {url}")
                
                try:
                    # Get metadata first
                    metadata = extract_platform_metadata(url)
                    title = metadata.get('title', f'{platform}_video_{video_num}')
                    
                    # Clean title for filename
                    clean_title = "".join(c for c in title if c.isalnum() or c in (' ', '-', '_'))[:50]
                    
                    video_result = {
                        'video_number': video_num,
                        'url': url,
                        'title': title,
                        'quality_tests': [],
                        'status': 'unknown'
                    }
                    
                    # Test different quality levels
                    for quality in self.quality_levels:
                        quality_result = self.test_quality_download(url, platform, clean_title, quality, video_num)
                        video_result['quality_tests'].append(quality_result)
                        
                        # If we successfully downloaded, break to avoid filling storage
                        if quality_result['status'] == 'success':
                            break
                    
                    # Check if any quality worked
                    successful_qualities = [q for q in video_result['quality_tests'] if q['status'] == 'success']
                    video_result['status'] = 'success' if successful_qualities else 'failed'
                    
                    platform_results.append(video_result)
                    
                except Exception as e:
                    error_result = {
                        'video_number': video_num,
                        'url': url,
                        'title': f'Unknown_{video_num}',
                        'quality_tests': [],
                        'status': 'error',
                        'error': str(e)
                    }
                    platform_results.append(error_result)
                    logging.error(f"❌ Video {video_num} failed: {e}")
                
                # Wait between videos to avoid rate limiting
                time.sleep(2)
            
            download_results[platform] = platform_results
        
        self.test_results['video_downloads'] = download_results

    def test_quality_download(self, url, platform, title, quality, video_num):
        """Test downloading a specific quality"""
        logging.info(f"  Testing {quality} quality...")
        
        quality_result = {
            'quality': quality,
            'status': 'unknown',
            'file_size_mb': 0,
            'download_time': 0,
            'cancelled_due_to_size': False,
            'error': None
        }
        
        try:
            # Create quality-specific config
            config = get_platform_config(platform)
            
            # Modify format selector for specific quality
            quality_formats = {
                '144p': 'worst[height<=144]/worst',
                '240p': 'worst[height<=240]/worst[height<=144]/worst',
                '360p': 'best[height<=360]/worst[height<=240]/worst',
                '480p': 'best[height<=480]/best[height<=360]/worst',
                '720p': 'best[height<=720]/best[height<=480]/best',
                '1080p': 'best[height<=1080]/best[height<=720]/best',
                '1440p': 'best[height<=1440]/best[height<=1080]/best',
                '2160p': 'best[height<=2160]/best[height<=1440]/best'
            }
            
            config['format'] = quality_formats.get(quality, 'best')
            config['outtmpl'] = os.path.join(self.test_dir, f'{title}_{quality}_{video_num}.%(ext)s')
            
            # Track download progress and file size
            downloaded_bytes = 0
            start_time = time.time()
            should_cancel = False
            
            def progress_hook(d):
                nonlocal downloaded_bytes, should_cancel
                if d['status'] == 'downloading':
                    downloaded_bytes = d.get('downloaded_bytes', 0)
                    
                    # Check if file is getting too large
                    if downloaded_bytes > (self.max_file_size_mb * 1024 * 1024):
                        should_cancel = True
                        logging.info(f"    Cancelling {quality} - file size exceeds {self.max_file_size_mb}MB")
                        quality_result['cancelled_due_to_size'] = True
                        return
            
            config['progress_hooks'] = [progress_hook]
            
            # Import yt_dlp for download
            import yt_dlp
            
            with yt_dlp.YoutubeDL(config) as ydl:
                # Check if formats are available first
                info = ydl.extract_info(url, download=False)
                
                if not info:
                    quality_result['status'] = 'no_info'
                    quality_result['error'] = 'Could not extract video info'
                    return quality_result
                
                formats = info.get('formats', [])
                if not formats:
                    quality_result['status'] = 'no_formats'
                    quality_result['error'] = 'No formats available'
                    return quality_result
                
                # Try to download
                try:
                    ydl.download([url])
                    download_time = time.time() - start_time
                    
                    # Find the downloaded file
                    filename = ydl.prepare_filename(info)
                    
                    if os.path.exists(filename):
                        file_size_mb = self.get_file_size_mb(filename)
                        
                        quality_result.update({
                            'status': 'success',
                            'file_size_mb': file_size_mb,
                            'download_time': f"{download_time:.2f}s",
                            'filename': filename
                        })
                        
                        logging.info(f"    ✓ {quality} - {file_size_mb}MB in {download_time:.2f}s")
                        
                        # Clean up immediately to save space
                        self.cleanup_downloaded_file(filename)
                        
                    else:
                        quality_result['status'] = 'file_not_found'
                        quality_result['error'] = 'Downloaded file not found'
                        
                except Exception as download_error:
                    if should_cancel or quality_result['cancelled_due_to_size']:
                        quality_result['status'] = 'cancelled_size'
                        quality_result['error'] = f'Cancelled - file size > {self.max_file_size_mb}MB'
                    else:
                        quality_result['status'] = 'download_failed'
                        quality_result['error'] = str(download_error)
                        
        except Exception as e:
            quality_result['status'] = 'error'
            quality_result['error'] = str(e)
            logging.info(f"    ❌ {quality} - {str(e)[:50]}")
        
        return quality_result

    def test_new_video_platforms(self):
        """Test new video hosting platforms"""
        logging.info("\n=== TESTING NEW VIDEO HOSTING PLATFORMS ===")
        
        new_platform_urls = [
            'https://deadtoons.upns.ink/#x6nwld',
            'https://cybervynx.com/e/3o7u7kkiyvt0',
            'https://voe.sx/e/ri04aimujjie',
            'https://filemoon.nl/e/85ncg6nmimic',
            'https://newer.stream/v/EKYal9A7BloF/',
            'https://short.icu/T0ZRB_67sXl',
            'https://smoothpre.com/s/t4isb3vrc564'
        ]
        
        new_platform_results = []
        
        for i, url in enumerate(new_platform_urls):
            logging.info(f"Testing Platform {i+1}: {url}")
            
            try:
                # Test platform detection
                platform = get_platform_from_url(url)
                display_name = get_platform_display_name(platform)
                
                result = {
                    'url': url,
                    'platform': platform,
                    'display_name': display_name,
                    'status': 'unknown'
                }
                
                # Test metadata extraction
                try:
                    metadata = extract_platform_metadata(url, platform)
                    result.update({
                        'status': 'success',
                        'title': metadata.get('title', 'N/A'),
                        'duration': metadata.get('duration', 'N/A')
                    })
                    logging.info(f"  ✓ Success: {metadata.get('title', 'N/A')[:50]}")
                    
                except Exception as meta_error:
                    result.update({
                        'status': 'metadata_failed',
                        'error': str(meta_error)
                    })
                    logging.info(f"  ❌ Metadata failed: {str(meta_error)[:50]}")
                
                new_platform_results.append(result)
                
            except Exception as e:
                result = {
                    'url': url,
                    'platform': 'unknown',
                    'display_name': 'Unknown',
                    'status': 'failed',
                    'error': str(e)
                }
                new_platform_results.append(result)
                logging.info(f"  ❌ Platform detection failed: {str(e)[:50]}")
            
            time.sleep(1)  # Rate limiting
        
        self.test_results['new_platforms'] = new_platform_results

    def test_direct_url_functionality(self):
        """Test direct URL detection and metadata extraction"""
        logging.info("\n=== TESTING DIRECT URL FUNCTIONALITY ===")
        
        direct_url_tests = [
            'https://sample-videos.com/zip/10/mp4/SampleVideo_720x480_1mb.mp4',
            'https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/BigBuckBunny.mp4',
            'https://file-examples.com/storage/fe6d99b7673e9e351ac5a1b/2017/10/file_example_MP4_480_1_5MG.mp4'
        ]
        
        direct_url_results = []
        
        for url in direct_url_tests:
            logging.info(f"Testing Direct URL: {url}")
            
            try:
                # Test platform detection
                platform = get_platform_from_url(url)
                is_direct = platform == 'direct_url'
                
                result = {
                    'url': url,
                    'detected_as_direct': is_direct,
                    'platform': platform,
                    'status': 'unknown'
                }
                
                if is_direct:
                    # Test metadata extraction
                    metadata = extract_platform_metadata(url)
                    result.update({
                        'status': 'success',
                        'title': metadata.get('title', 'N/A'),
                        'file_size': metadata.get('file_size', 'Unknown'),
                        'quality': metadata.get('quality', 'Unknown'),
                        'format': metadata.get('format', 'Unknown')
                    })
                    logging.info(f"  ✓ Direct URL detected and processed")
                else:
                    result.update({
                        'status': 'not_detected_as_direct',
                        'error': f'Detected as {platform} instead of direct_url'
                    })
                    logging.info(f"  ❌ Not detected as direct URL (detected as {platform})")
                
                direct_url_results.append(result)
                
            except Exception as e:
                result = {
                    'url': url,
                    'detected_as_direct': False,
                    'platform': 'unknown',
                    'status': 'error',
                    'error': str(e)
                }
                direct_url_results.append(result)
                logging.info(f"  ❌ Error: {str(e)[:50]}")
        
        self.test_results['direct_urls'] = direct_url_results

    def run_comprehensive_test(self):
        """Run all tests in sequence"""
        logging.info("🧪 STARTING COMPREHENSIVE VIDEO TESTING")
        logging.info("=" * 60)
        
        start_time = time.time()
        
        try:
            # Run all test modules
            self.test_platform_detection()
            self.test_metadata_extraction()
            self.test_video_downloading_with_quality()
            self.test_new_video_platforms()
            self.test_direct_url_functionality()
            
            # Generate summary
            end_time = time.time()
            total_time = end_time - start_time
            
            self.generate_test_summary(total_time)
            self.save_test_results()
            
        except KeyboardInterrupt:
            logging.info("\n⏹️ Testing stopped by user")
        except Exception as e:
            logging.error(f"\n💥 Testing failed: {e}")
        finally:
            # Cleanup test directory
            self.cleanup_test_directory()

    def generate_test_summary(self, total_time):
        """Generate and display test summary"""
        logging.info("\n" + "=" * 60)
        logging.info("📊 COMPREHENSIVE TEST SUMMARY")
        logging.info("=" * 60)
        
        # Platform Detection Summary
        detection_data = self.test_results.get('platform_detection', {})
        logging.info(f"🔍 Platform Detection: {detection_data.get('accuracy', 'N/A')} accuracy")
        
        # Metadata Extraction Summary
        metadata_data = self.test_results.get('metadata_extraction', {})
        logging.info(f"📋 Metadata Extraction: {metadata_data.get('success_rate', 'N/A')} success rate")
        
        # Video Downloads Summary
        download_data = self.test_results.get('video_downloads', {})
        total_videos = 0
        successful_videos = 0
        
        for platform, videos in download_data.items():
            total_videos += len(videos)
            successful_videos += len([v for v in videos if v['status'] == 'success'])
        
        download_success_rate = (successful_videos / total_videos * 100) if total_videos > 0 else 0
        logging.info(f"📥 Video Downloads: {successful_videos}/{total_videos} successful ({download_success_rate:.1f}%)")
        
        # New Platforms Summary
        new_platforms_data = self.test_results.get('new_platforms', [])
        new_success = len([p for p in new_platforms_data if p['status'] == 'success'])
        logging.info(f"🆕 New Platforms: {new_success}/{len(new_platforms_data)} successful")
        
        # Direct URLs Summary
        direct_urls_data = self.test_results.get('direct_urls', [])
        direct_success = len([d for d in direct_urls_data if d['status'] == 'success'])
        logging.info(f"🔗 Direct URLs: {direct_success}/{len(direct_urls_data)} successful")
        
        logging.info(f"⏱️ Total Test Time: {total_time:.2f} seconds")
        logging.info("=" * 60)

    def save_test_results(self):
        """Save test results to JSON file"""
        try:
            results_file = 'test_results/comprehensive_test_results.json'
            with open(results_file, 'w', encoding='utf-8') as f:
                json.dump(self.test_results, f, indent=2, ensure_ascii=False)
            
            logging.info(f"💾 Test results saved to: {results_file}")
            
        except Exception as e:
            logging.error(f"Failed to save test results: {e}")

    def cleanup_test_directory(self):
        """Clean up test directory"""
        try:
            if os.path.exists(self.test_dir):
                shutil.rmtree(self.test_dir)
                logging.info(f"🧹 Cleaned up test directory: {self.test_dir}")
        except Exception as e:
            logging.warning(f"Failed to cleanup test directory: {e}")


def main():
    """Main function to run comprehensive tests"""
    print("🎬 Comprehensive Video Platform Tester")
    print("=" * 50)
    print("This script will test:")
    print("• Platform detection accuracy")
    print("• Metadata extraction from multiple platforms")
    print("• Video downloading with quality management")
    print("• New video hosting platforms")
    print("• Direct URL functionality")
    print("• File size management (cancels downloads > 300MB)")
    print("=" * 50)
    
    # Ask user confirmation
    try:
        response = input("Do you want to start the comprehensive test? (y/N): ").lower()
        if response not in ['y', 'yes']:
            print("Test cancelled by user.")
            return
    except KeyboardInterrupt:
        print("\nTest cancelled by user.")
        return
    
    # Create and run tester
    tester = ComprehensiveVideoTester()
    tester.run_comprehensive_test()
    
    print("\n✅ Comprehensive testing completed!")
    print("Check 'test_results/comprehensive_test_results.json' for detailed results.")


if __name__ == "__main__":
    main()
