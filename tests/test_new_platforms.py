#!/usr/bin/env python3

import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from multi_platform_downloader import get_platform_from_url, extract_platform_metadata, get_platform_display_name


def test_new_video_platforms():
    """Test new video hosting platforms"""

    test_urls = [
        'https://deadtoons.upns.ink/#x6nwld',
        'https://cybervynx.com/e/3o7u7kkiyvt0',
        'https://voe.sx/e/ri04aimujjie', 'https://filemoon.nl/e/85ncg6nmimic',
        'https://newer.stream/v/EKYal9A7BloF/',
        'https://short.icu/T0ZRB_67sXl',
        'https://www.youtube.com/embed/ZMpfkJiQrGg',
        'https://smoothpre.com/s/t4isb3vrc564'
    ]

    results = []

    print("Testing New Video Hosting Platforms")
    print("=" * 50)

    for i, url in enumerate(test_urls):
        try:
            print(f"\nTest {i+1}: {url}")

            # Test platform detection
            platform = get_platform_from_url(url)
            display_name = get_platform_display_name(platform)
            print(f"  Platform detected: {display_name} ({platform})")

            # Test metadata extraction
            try:
                metadata = extract_platform_metadata(url, platform)
                print(f"  ✓ Metadata extraction successful")
                print(f"    Title: {metadata.get('title', 'N/A')[:50]}...")
                print(f"    Duration: {metadata.get('duration', 'N/A')}")

                results.append({
                    'url': url,
                    'platform': platform,
                    'display_name': display_name,
                    'status': 'success',
                    'title': metadata.get('title', 'N/A'),
                    'duration': metadata.get('duration', 'N/A')
                })

            except Exception as meta_error:
                print(
                    f"  ❌ Metadata extraction failed: {str(meta_error)[:100]}")
                results.append({
                    'url': url,
                    'platform': platform,
                    'display_name': display_name,
                    'status': 'metadata_failed',
                    'error': str(meta_error)
                })

        except Exception as e:
            print(f"  ❌ Platform detection failed: {str(e)[:100]}")
            results.append({
                'url': url,
                'platform': 'unknown',
                'display_name': 'Unknown',
                'status': 'failed',
                'error': str(e)
            })

    # Summary
    print("\n" + "=" * 50)
    print("TEST SUMMARY")
    print("=" * 50)

    success_count = len([r for r in results if r['status'] == 'success'])
    metadata_failed = len(
        [r for r in results if r['status'] == 'metadata_failed'])
    failed_count = len([r for r in results if r['status'] == 'failed'])

    print(f"Total URLs tested: {len(test_urls)}")
    print(f"✓ Successful: {success_count}")
    print(f"⚠ Metadata failed: {metadata_failed}")
    print(f"❌ Failed: {failed_count}")

    return results


if __name__ == "__main__":
    test_new_video_platforms()
