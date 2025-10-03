
import requests
import json
import time
import feedparser
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_sohel_channel():
    """Test monitoring for channel using YouTube API v3 and RSS"""
    channel_url = "https://www.youtube.com/@aajtak"
    channel_id = "UCt4t-jeY85JegMlZ-E5UWtA"  # From your channels.json
    
    print(f"🧪 Testing channel monitoring for: {channel_url}")
    print(f"📺 Channel ID: {channel_id}")
    
    # Test YouTube API v3
    print("\n🔍 Testing YouTube API v3...")
    api_key = os.environ.get('YOUTUBE_API_KEY')
    
    if api_key:
        try:
            # Test channel info
            api_url = 'https://www.googleapis.com/youtube/v3/channels'
            params = {
                'part': 'snippet,statistics',
                'id': channel_id,
                'key': api_key
            }
            
            response = requests.get(api_url, params=params)
            response.raise_for_status()
            
            data = response.json()
            
            if data.get('items'):
                channel_info = data['items'][0]
                snippet = channel_info['snippet']
                statistics = channel_info['statistics']
                
                print(f"✅ YouTube API working!")
                print(f"   📺 Channel Name: {snippet.get('title', 'Unknown')}")
                print(f"   👥 Subscribers: {statistics.get('subscriberCount', 'Unknown')}")
                print(f"   🎥 Total Videos: {statistics.get('videoCount', 'Unknown')}")
                print(f"   👁️ Total Views: {statistics.get('viewCount', 'Unknown')}")
            else:
                print("❌ No channel data found via API")
                
        except Exception as e:
            print(f"❌ YouTube API test failed: {e}")
    else:
        print("⚠️ No YouTube API key found in environment")
    
    # Test latest videos via API
    print("\n🔍 Testing latest videos via YouTube API...")
    if api_key:
        try:
            api_url = 'https://www.googleapis.com/youtube/v3/search'
            params = {
                'part': 'snippet',
                'channelId': channel_id,
                'order': 'date',
                'type': 'video',
                'maxResults': 3,
                'key': api_key
            }
            
            response = requests.get(api_url, params=params)
            response.raise_for_status()
            
            data = response.json()
            
            if data.get('items'):
                print(f"✅ Found {len(data['items'])} recent videos via API:")
                for i, item in enumerate(data['items']):
                    print(f"   {i+1}. {item['snippet']['title']}")
                    print(f"      Published: {item['snippet']['publishedAt']}")
            else:
                print("❌ No recent videos found via API")
                
        except Exception as e:
            print(f"❌ Latest videos API test failed: {e}")
    
    # Test RSS feed as fallback
    print("\n🔍 Testing RSS feed...")
    try:
        rss_url = f"https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}"
        feed = feedparser.parse(rss_url)
        
        if feed.entries:
            print(f"✅ RSS feed working! Found {len(feed.entries)} recent videos")
            for i, entry in enumerate(feed.entries[:3]):
                print(f"   {i+1}. {entry.title} - {entry.published}")
        else:
            print("❌ No videos found in RSS feed")
    except Exception as e:
        print(f"❌ RSS test failed: {e}")
    
    # Test monitoring simulation
    print(f"\n🔄 Testing video count monitoring...")
    try:
        # Try API first, then RSS
        current_count = 0
        
        if api_key:
            try:
                api_url = 'https://www.googleapis.com/youtube/v3/channels'
                params = {
                    'part': 'statistics',
                    'id': channel_id,
                    'key': api_key
                }
                
                response = requests.get(api_url, params=params)
                if response.status_code == 200:
                    data = response.json()
                    if data.get('items'):
                        current_count = int(data['items'][0]['statistics'].get('videoCount', 0))
                        print(f"📊 Current video count (API): {current_count}")
                    else:
                        raise Exception("No data")
                else:
                    raise Exception(f"Status {response.status_code}")
                    
            except Exception:
                # Fallback to RSS
                feed = feedparser.parse(rss_url)
                current_count = len(feed.entries) if feed.entries else 0
                print(f"📊 Current video count (RSS fallback): {current_count}")
        else:
            # Use RSS only
            feed = feedparser.parse(rss_url)
            current_count = len(feed.entries) if feed.entries else 0
            print(f"📊 Current video count (RSS): {current_count}")
        
        # Simulate monitoring
        print("⏱️  Starting 30-second monitoring test...")
        initial_count = current_count
        
        for i in range(3):
            time.sleep(10)
            
            # Check via API if available
            if api_key:
                try:
                    api_url = 'https://www.googleapis.com/youtube/v3/channels'
                    params = {
                        'part': 'statistics',
                        'id': channel_id,
                        'key': api_key
                    }
                    
                    response = requests.get(api_url, params=params)
                    if response.status_code == 200:
                        data = response.json()
                        if data.get('items'):
                            new_count = int(data['items'][0]['statistics'].get('videoCount', 0))
                        else:
                            raise Exception("No data")
                    else:
                        raise Exception(f"Status {response.status_code}")
                        
                except Exception:
                    # Fallback to RSS
                    feed = feedparser.parse(rss_url)
                    new_count = len(feed.entries) if feed.entries else 0
            else:
                # RSS only
                feed = feedparser.parse(rss_url)
                new_count = len(feed.entries) if feed.entries else 0
            
            print(f"[{i+1}/3] Count: {new_count} (change: {new_count - initial_count})", flush=True)
            
            if new_count != initial_count:
                print("🎉 VIDEO COUNT CHANGED DETECTED!", flush=True)
                break
        
    except Exception as e:
        print(f"❌ Monitoring test failed: {e}")

if __name__ == "__main__":
    test_sohel_channel()
