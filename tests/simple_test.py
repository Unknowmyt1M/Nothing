from multi_platform_downloader import extract_platform_metadata, get_platform_from_url, get_platform_display_name

def run_simple_test():
    """Simple test of core functionality with reliable platforms"""
    
    test_urls = [
        'https://www.youtube.com/watch?v=jNQXAC9IVRw',  # Me at the zoo
        'https://www.dailymotion.com/video/x7tgad0',    # Dailymotion demo
        'https://www.youtube.com/watch?v=9bZkp7q19f0'   # Gangnam Style  
    ]
    
    results = []
    
    for i, url in enumerate(test_urls):
        try:
            platform = get_platform_from_url(url)
            metadata = extract_platform_metadata(url)
            
            results.append({
                'test_number': i + 1,
                'url': url,
                'platform': get_platform_display_name(platform),
                'status': 'success',
                'title': metadata.get('title', 'N/A')[:50] + '...',
                'uploader': metadata.get('uploader', 'N/A'),
                'duration': metadata.get('duration', 'N/A')
            })
        except Exception as e:
            results.append({
                'test_number': i + 1,
                'url': url,
                'platform': get_platform_display_name(get_platform_from_url(url)),
                'status': 'failed',
                'error': str(e)[:100] + '...'
            })
    
    return results