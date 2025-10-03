import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse, parse_qs
from concurrent.futures import ThreadPoolExecutor
import json

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36'
}

def get_episode_links(anime_url):
    print("[+] Crawling anime page for episode URLs...")
    response = requests.get(anime_url, headers=headers)
    if response.status_code != 200:
        print("[!] Failed to load anime page!")
        return []
    
    soup = BeautifulSoup(response.text, 'html.parser')
    episode_links = []
    
    for a_tag in soup.find_all('a', href=True):
        href = a_tag['href']
        if href.startswith('https://luciferdonghua.in/') and '-episode-' in href and href.endswith('-lucifer-donghua/'):
            if href not in episode_links:
                episode_links.append(href)
    
    print(f"[+] Found {len(episode_links)} episode links.")
    return episode_links

def extract_episode_data(episode_url):
    print(f"    [*] Processing: {episode_url}")
    result = {
        'episode_url': episode_url,
        'dailymotion_url': None,
        'video_id': None,
        'title': None,
        'upload_date': None
    }

    try:
        response = requests.get(episode_url, headers=headers)
        if response.status_code != 200:
            print(f"    [!] Failed to load {episode_url}")
            return result

        soup = BeautifulSoup(response.text, 'html.parser')

        # Extract Dailymotion embed video ID
        meta_tag = soup.find('meta', attrs={'itemprop': 'embedUrl'})
        if meta_tag:
            embed_url = meta_tag.get('content')
            parsed = urlparse(embed_url)
            query_params = parse_qs(parsed.query)
            video_id = query_params.get('video')
            if video_id:
                result['video_id'] = video_id[0]
                result['dailymotion_url'] = f"https://www.dailymotion.com/video/{video_id[0]}"

        # Extract episode title
        title_tag = soup.find('meta', attrs={'property': 'og:title'})
        if title_tag:
            result['title'] = title_tag.get('content')

        # Extract upload date
        date_tag = soup.find('meta', attrs={'itemprop': 'uploadDate'})
        if date_tag:
            result['upload_date'] = date_tag.get('content')

    except Exception as e:
        print(f"    [!] Error processing {episode_url}: {e}")

    return result

def main():
    anime_url = input("🚀 Enter anime URL (ex: https://luciferdonghua.in/anime/veiled-dreams-2025/):\n").strip()
    episode_links = get_episode_links(anime_url)

    final_data = []
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(extract_episode_data, url) for url in episode_links]
        for future in futures:
            result = future.result()
            if result['dailymotion_url']:
                print(f"    ✅ Found: {result['dailymotion_url']}")
            else:
                print(f"    ❌ No Dailymotion URL in {result['episode_url']}")
            final_data.append(result)

    # Save to JSON file
    with open('dailymotion_videos.json', 'w', encoding='utf-8') as f:
        json.dump(final_data, f, indent=4)

    print("\n🔥 Extraction complete! Data saved in dailymotion_videos.json")

if __name__ == '__main__':
    main()
