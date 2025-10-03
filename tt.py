
import requests
import json
import time
import feedparser
from auth_helper import get_youtube_api_service
import os

def test_sohel_channel():
    """Test monitoring for SOHEL HACKS V2 channel"""
    channel_url = "https://www.youtube.com/@aajtak"
    channel_id = "UCt4t-jeY85JegMlZ-E5UWtA"  # From your channels.json

    print(f"🧪 Testing channel monitoring for: {channel_url}")
    print(f"📺 Channel ID: {channel_id}")

    # Test RSS feed
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

    # Test direct channel check
    print(f"\n🔄 Testing video count monitoring...")
    try:
        current_count = len(feed.entries) if feed.entries else 0
        print(f"📊 Current video count: {current_count}")

        # Simulate monitoring
        print("⏱️  Starting 30-second monitoring test...")
        initial_count = current_count

        for i in range(3):
            time.sleep(10)
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
