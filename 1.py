import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse, parse_qs

def get_episode_links(anime_url):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36'
    }
    print("[+] Crawling anime page for episode URLs...")
    response = requests.get(anime_url, headers=headers)
    if response.status_code != 200:
        print("[!] Failed to load anime page!")
        return []
    
    soup = BeautifulSoup(response.text, 'html.parser')
    episode_links = []
    
    # Exactly jo pattern tera screenshot dikha raha tha
    for a_tag in soup.find_all('a', href=True):
        href = a_tag['href']
        if href.startswith('https://luciferdonghua.in/') and '-episode-' in href and href.endswith('-lucifer-donghua/'):
            if href not in episode_links:
                episode_links.append(href)
    
    print(f"[+] Found {len(episode_links)} episode links.")
    return episode_links

def extract_dailymotion_video_id(episode_url):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36'
    }
    print(f"    [*] Crawling episode page: {episode_url}")
    response = requests.get(episode_url, headers=headers)
    if response.status_code != 200:
        print("    [!] Failed to load episode page.")
        return None
    
    soup = BeautifulSoup(response.text, 'html.parser')
    meta_tag = soup.find('meta', attrs={'itemprop': 'embedUrl'})
    if meta_tag:
        embed_url = meta_tag.get('content')
        parsed = urlparse(embed_url)
        query_params = parse_qs(parsed.query)
        video_id = query_params.get('video')
        if video_id:
            return video_id[0]
    return None

def main():
    anime_url = input("🚀 Enter anime URL (ex: https://luciferdonghua.in/anime/veiled-dreams-2025/):\n").strip()
    episode_links = get_episode_links(anime_url)

    final_dailymotion_urls = []
    for idx, ep_url in enumerate(episode_links, 1):
        print(f"\n[+] Processing Episode {idx}/{len(episode_links)}")
        video_id = extract_dailymotion_video_id(ep_url)
        if video_id:
            final_url = f"https://www.dailymotion.com/video/{video_id}"
            print(f"    ✅ Found: {final_url}")
            final_dailymotion_urls.append(final_url)
        else:
            print("    ❌ No Dailymotion video found in this episode.")

    print("\n🔥 All Extracted Dailymotion URLs:")
    for url in final_dailymotion_urls:
        print(url)

if __name__ == '__main__':
    main()
