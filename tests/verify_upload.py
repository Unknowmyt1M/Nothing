import os
import sys
import json
import logging

# Add root folder to import paths
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend.auth_helper import refresh_access_token, get_youtube_channel_info, get_user_info
from backend.json_db import get_user_tokens, store_user_tokens

def main():
    print("=== Testing Backend YouTube Upload / Auth Pipeline ===")
    
    user_id = "helloadi777_gmail_com"
    print(f"Loading tokens for user: {user_id}")
    
    tokens = get_user_tokens(user_id)
    if not tokens:
        print("[ERROR] No tokens found in database for user helloadi777_gmail_com.")
        return
        
    access_token = tokens.get('access_token')
    refresh_token = tokens.get('refresh_token')
    
    print("Attempting to get user profile details from Google...")
    try:
        user_info = get_user_info(access_token)
        print(f"[OK] Connected Google Profile Name: {user_info.get('name')}")
        print(f"[OK] Email: {user_info.get('email')}")
    except Exception as e:
        print(f"[WARNING] Access token expired or invalid: {e}")
        if refresh_token:
            print("Attempting to refresh access token using refresh_token...")
            try:
                new_access_token = refresh_access_token(refresh_token)
                print("[OK] Successfully refreshed access token!")
                # Update token in db
                store_user_tokens(user_id, new_access_token, refresh_token)
                access_token = new_access_token
                
                # Fetch profile details again
                user_info = get_user_info(access_token)
                print(f"[OK] Connected Google Profile Name: {user_info.get('name')}")
                print(f"[OK] Email: {user_info.get('email')}")
            except Exception as re:
                print(f"[ERROR] Failed to refresh access token: {re}")
                return
        else:
            print("[ERROR] No refresh token available. User must re-authenticate.")
            return
            
    print("Fetching YouTube Channel details using access token...")
    try:
        channel_info = get_youtube_channel_info(access_token)
        print(f"[OK] YouTube Channel Name: {channel_info.get('name')}")
        print(f"[OK] Subscribers: {channel_info.get('subscribers')}")
        print(f"[OK] Video Count: {channel_info.get('video_count')}")
        print(f"[OK] View Count: {channel_info.get('view_count')}")
        print("[OK] YouTube authentication and channel access are fully functional!")
    except Exception as e:
        print(f"[ERROR] Failed to fetch YouTube channel info: {e}")
        print("[ERROR] Check if the YouTube channel is enabled and has permission.")

if __name__ == "__main__":
    main()
