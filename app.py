import os
import json
import logging
from flask import Flask, render_template, request, redirect, url_for, session, jsonify, flash
from werkzeug.middleware.proxy_fix import ProxyFix
import requests
from auth_helper import get_google_auth_url, handle_google_callback, get_user_info, refresh_access_token
from yt_metadata import extract_metadata
from yt_uploader import download_and_upload_video, get_download_progress
from multi_platform_downloader import (
    extract_platform_metadata, 
    download_and_upload_multi_platform, 
    get_platform_from_url, 
    is_platform_supported, 
    get_supported_platforms,
    get_platform_display_name
)
import threading
import time
from dotenv import load_dotenv
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import smtplib
try:
    import markdown
except ImportError:
    logging.warning("markdown library not installed. Static pages will not render properly.")
    # Fallback: create a dummy markdown function
    class markdown:
        @staticmethod
        def markdown(text):
            return f"<pre>{text}</pre>"

# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.DEBUG)

app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "dev-secret-key-change-in-production")
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

# Global progress tracking
progress_data = {}

@app.context_processor
def inject_user_context():
    """Inject user and YouTube channel info into all templates"""
    user_info = None
    youtube_channel = None
    
    if 'access_token' in session:
        try:
            from auth_helper import get_youtube_channel_info
            user_info = get_user_info(session['access_token'])
            # Update session with email-based user_id if not already set
            if 'user_id' not in session or '@' in session.get('user_id', ''):
                user_email_dir = user_info['email'].replace('@', '_').replace('.', '_')
                session['user_id'] = user_email_dir
            # Try to get YouTube channel info
            try:
                youtube_channel = get_youtube_channel_info(session['access_token'])
            except Exception:
                pass  # Channel info is optional
        except Exception:
            pass  # User info failed, keep None
    
    return {
        'current_user_info': user_info,
        'current_youtube_channel': youtube_channel,
        'os': os  # Make os module available in templates
    }

@app.route('/')
def home():
    """Home page with video upload functionality"""
    return render_template('home.html')

@app.route('/accounts')
def accounts():
    """Accounts page for Google OAuth management"""
    user_info = None
    youtube_channel = None
    if 'access_token' in session:
        try:
            from auth_helper import get_youtube_channel_info
            user_info = get_user_info(session['access_token'])
            # Try to get YouTube channel info
            try:
                youtube_channel = get_youtube_channel_info(session['access_token'])
            except Exception as yt_e:
                logging.warning(f"Could not fetch YouTube channel info: {yt_e}")
        except Exception as e:
            logging.error(f"Error getting user info: {e}")
            session.clear()

    return render_template('accounts.html', user_info=user_info, youtube_channel=youtube_channel)

@app.route('/metadata')
def metadata():
    """Metadata extraction page"""
    return render_template('metadata.html')

@app.route('/extract_metadata', methods=['POST'])
def extract_metadata_route():
    """Extract metadata from any supported platform URL"""
    url = request.form.get('url')
    if not url:
        return jsonify({'error': 'No URL provided'}), 400

    try:
        # Check if platform is supported
        if not is_platform_supported(url):
            platform = get_platform_from_url(url)
            return jsonify({'error': f'Platform "{platform}" is not supported yet'}), 400

        # Use multi-platform metadata extraction
        metadata = extract_platform_metadata(url)
        return jsonify(metadata)
    except Exception as e:
        logging.error(f"Error extracting metadata: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/get_video_qualities', methods=['POST'])
def get_video_qualities():
    """Get available video qualities and file sizes"""
    try:
        url = request.form.get('url')
        if not url:
            return jsonify({'error': 'No URL provided'}), 400

        from multi_platform_downloader import get_video_qualities_info
        qualities = get_video_qualities_info(url)
        
        return jsonify({'qualities': qualities, 'success': True})

    except Exception as e:
        logging.error(f"Error getting video qualities: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/download_video', methods=['POST'])
def download_video():
    """Start video download with selected quality"""
    url = request.form.get('url')
    quality = request.form.get('quality')
    
    if not url:
        return jsonify({'error': 'No URL provided'}), 400
    
    if not quality:
        return jsonify({'error': 'No quality selected'}), 400

    # Generate unique download ID
    download_id = f"download_{int(time.time())}_{hash(url) % 10000}"
    
    # Initialize progress tracking
    progress_data[download_id] = {
        'status': 'starting',
        'progress': 0,
        'speed': '0 Mbps',
        'eta': '--:--',
        'downloaded': '0 B',
        'total': '0 B',
        'filename': None
    }

    def download_worker():
        try:
            from multi_platform_downloader import download_video_with_progress
            result = download_video_with_progress(url, quality, download_id, progress_data)
            
            progress_data[download_id].update({
                'status': 'completed',
                'progress': 100,
                'filename': result.get('filename'),
                'file_path': result.get('file_path')
            })
        except Exception as e:
            logging.error(f"Download error: {e}")
            progress_data[download_id].update({
                'status': 'error',
                'error': str(e)
            })

    # Start download in background thread
    thread = threading.Thread(target=download_worker)
    thread.daemon = True
    thread.start()

    return jsonify({'download_id': download_id})

@app.route('/download_progress/<download_id>')
def download_progress(download_id):
    """Get download progress"""
    if download_id not in progress_data:
        return jsonify({'error': 'Download not found'}), 404
    
    return jsonify(progress_data[download_id])

@app.route('/google_login')
def google_login():
    """Initiate Google OAuth login"""
    auth_url = get_google_auth_url()
    return redirect(auth_url)

@app.route('/google_login/callback')
def google_callback():
    """Handle Google OAuth callback"""
    code = request.args.get('code')
    if not code:
        flash('Authorization failed', 'error')
        return redirect(url_for('accounts'))

    try:
        tokens = handle_google_callback(code)
        session['access_token'] = tokens['access_token']
        session['refresh_token'] = tokens.get('refresh_token')

        # Get user info and store tokens in MongoDB
        user_info = get_user_info(tokens['access_token'])
        user_email_dir = user_info['email'].replace('@', '_').replace('.', '_')
        session['user_id'] = user_email_dir
        session['user_name'] = user_info['name']
        session['user_email'] = user_info['email']

        # Store tokens for background automation in MongoDB
        from mongo import store_user_tokens as mongo_store_tokens, save_oauth_tokens
        
        # Store access/refresh tokens using asyncio.run() in a new event loop
        try:
            # Create a new event loop for this operation
            import asyncio
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                loop.run_until_complete(mongo_store_tokens(user_email_dir, tokens['access_token'], tokens.get('refresh_token')))
                # Also store full token.json data
                loop.run_until_complete(save_oauth_tokens(user_email_dir, tokens))
                logging.info(f"✅ Successfully stored tokens for user {user_email_dir}")
            finally:
                loop.close()
        except Exception as token_error:
            logging.error(f"❌ Failed to store tokens: {token_error}")
            flash('Account connected but token storage failed', 'warning')

        flash('Successfully connected to Google account!', 'success')
        return redirect(url_for('accounts'))
    except Exception as e:
        logging.error(f"Error in Google callback: {e}")
        flash('Failed to connect Google account', 'error')
        return redirect(url_for('accounts'))

@app.route('/logout')
def logout():
    """Logout user and clear session"""
    session.clear()
    flash('Successfully logged out', 'success')
    return redirect(url_for('accounts'))

@app.route('/upload_video', methods=['POST'])
def upload_video():
    """Start video upload process"""
    if 'access_token' not in session:
        return jsonify({'error': 'Not authenticated'}), 401

    url = request.form.get('url')
    title = request.form.get('title')
    description = request.form.get('description')
    tags = request.form.get('tags', '').split(',') if request.form.get('tags') else []
    privacy = request.form.get('privacy', 'public')

    if not url:
        return jsonify({'error': 'No URL provided'}), 400

    # Start upload in background thread
    user_email_dir = get_user_id()  # This now returns email-based directory name
    upload_id = f"{user_email_dir}_{int(time.time())}"

    # Extract session data before starting background thread
    current_access_token = session.get('access_token')
    current_refresh_token = session.get('refresh_token')

    progress_data[upload_id] = {
        'status': 'starting',
        'progress': 0,
        'speed': '0 MiB/s',
        'downloaded': '0 MiB',
        'total': '0 MiB'
    }

    def upload_worker():
        with app.app_context():
            try:
                access_token = current_access_token

                # Refresh token if needed
                if current_refresh_token:
                    try:
                        new_access_token = refresh_access_token(current_refresh_token)
                        access_token = new_access_token
                    except Exception as e:
                        logging.error(f"Token refresh error: {e}")
                        # Continue with original token if refresh fails

                # Check if platform is supported
                if not is_platform_supported(url):
                    platform = get_platform_from_url(url)
                    raise Exception(f'Platform "{platform}" is not supported yet')

                # Use multi-platform downloader
                result = download_and_upload_multi_platform(
                    url, 
                    access_token, 
                    user_email_dir, 
                    title, 
                    description, 
                    tags,
                    privacy,
                    upload_id,
                    progress_data
                )
                progress_data[upload_id]['result'] = result
            except Exception as e:
                logging.error(f"Upload error: {e}")
                progress_data[upload_id]['error'] = str(e)
                progress_data[upload_id]['status'] = 'error'

    thread = threading.Thread(target=upload_worker)
    thread.daemon = True
    thread.start()

    return jsonify({'upload_id': upload_id})

@app.route('/upload_progress/<upload_id>')
def upload_progress(upload_id):
    """Get upload progress"""
    if upload_id in progress_data:
        return jsonify(progress_data[upload_id])
    else:
        return jsonify({'error': 'Upload not found'}), 404

@app.route('/test_metadata')
def test_metadata():
    """Test metadata extraction with different platforms"""
    # Test URLs from different platforms
    test_urls = [
        'https://www.youtube.com/watch?v=jNQXAC9IVRw',  # YouTube
        'https://vimeo.com/148751763',  # Vimeo
        'https://www.dailymotion.com/video/x7tgad0',  # Dailymotion
        'https://www.reddit.com/r/videos/comments/sample',  # Reddit (example)
    ]

    results = []

    for i, url in enumerate(test_urls):
        try:
            logging.info(f"Testing metadata extraction for URL {i+1}: {url}")
            platform = get_platform_from_url(url)
            metadata = extract_platform_metadata(url)
            results.append({
                'url': url,
                'platform': platform,
                'status': 'success',
                'title': metadata.get('title', 'Unknown'),
                'uploader': metadata.get('uploader', 'Unknown'),
                'duration': metadata.get('duration', 'Unknown'),
                'view_count': metadata.get('view_count', 'Unknown')
            })
        except Exception as e:
            results.append({
                'url': url,
                'platform': get_platform_from_url(url),
                'status': 'error',
                'error': str(e)
            })
            logging.error(f"Metadata test error for {url}: {e}")

    html_results = "<h2>Metadata Extraction Test Results</h2><ul>"
    for result in results:
        status_color = "green" if result['status'] == 'success' else "red"
        html_results += f'<li style="color: {status_color};">'
        html_results += f"<strong>Status:</strong> {result['status']}<br>"
        html_results += f"<strong>URL:</strong> {result['url']}<br>"

        if result['status'] == 'success':
            html_results += f"<strong>Platform:</strong> {get_platform_display_name(result.get('platform', 'unknown'))}<br>"
            html_results += f"<strong>Title:</strong> {result.get('title', 'Unknown')}<br>"
            html_results += f"<strong>Uploader:</strong> {result.get('uploader', 'Unknown')}<br>"
            html_results += f"<strong>Duration:</strong> {result.get('duration', 'Unknown')}<br>"
            html_results += f"<strong>Views:</strong> {result.get('view_count', 'Unknown')}<br>"
        else:
            html_results += f"<strong>Error:</strong> {result.get('error', 'Unknown error')}<br>"

        html_results += "</li><br>"

    html_results += "</ul>"
    html_results += f"<p><strong>Total Tests:</strong> {len(results)}</p>"
    successful = len([r for r in results if r['status'] == 'success'])
    html_results += f"<p><strong>Successful:</strong> {successful}/{len(results)}</p>"

    return html_results

@app.route('/test_download_single')
def test_download_single():
    """Test a single video download"""
    # Test with a very small, reliable video
    test_url = 'https://www.youtube.com/watch?v=jNQXAC9IVRw'  # First YouTube video - very short

    try:
        from yt_uploader import test_video_download
        results = test_video_download([test_url], "single_test")

        if results and len(results) > 0:
            result = results[0]
            if result['status'] == 'success':
                return f"<h2>Single Download Test: SUCCESS</h2><p>Title: {result.get('title')}<br>File Size: {result.get('file_size')}<br>Video was downloaded and deleted automatically.</p>"
            else:
                return f"<h2>Single Download Test: FAILED</h2><p>Error: {result.get('error')}</p>"
        else:
            return "<h2>Single Download Test: NO RESULTS</h2>"

    except Exception as e:
        return f"<h2>Single Download Test: ERROR</h2><p>{str(e)}</p>"

@app.route('/test_vimeo')
def test_vimeo():
    """Test Vimeo functionality with provided cookies"""
    html_result = "<h2>Vimeo Test with Provided Cookies</h2>"

    # Check if Vimeo cookies exist
    vimeo_cookies_file = "cookies/vimeo_cookies.txt"
    cookies_exist = os.path.exists(vimeo_cookies_file)

    if cookies_exist:
        html_result += f"<p style='color: green;'>✓ Vimeo cookies file found: {vimeo_cookies_file}</p>"

        try:
            with open(vimeo_cookies_file, 'r') as f:
                content = f.read()
                lines_count = len([line for line in content.split('\n') if line.strip() and not line.startswith('#')])
                has_vimeo_session = 'vimeo' in content
                has_cf_clearance = 'cf_clearance' in content

                html_result += f"<p>Total cookies: {lines_count}</p>"
                html_result += f"<p style='color: {'green' if has_vimeo_session else 'orange'};'>{'✓' if has_vimeo_session else '?'} Vimeo session data: {has_vimeo_session}</p>"
                html_result += f"<p style='color: {'green' if has_cf_clearance else 'orange'};'>{'✓' if has_cf_clearance else '?'} Cloudflare clearance: {has_cf_clearance}</p>"

        except Exception as e:
            html_result += f"<p style='color: red;'>✗ Error reading cookies: {e}</p>"
    else:
        html_result += f"<p style='color: red;'>✗ Vimeo cookies file not found</p>"

    html_result += "<hr><h3>Vimeo Metadata Test</h3>"

    # Test with a sample Vimeo URL
    try:
        from multi_platform_downloader import extract_platform_metadata
        test_url = "https://vimeo.com/336812686"
        metadata = extract_platform_metadata(test_url, 'vimeo')

        html_result += f"<p style='color: green;'>✓ Vimeo metadata extraction successful!</p>"
        html_result += f"<p><strong>Title:</strong> {metadata.get('title', 'Unknown')}</p>"
        html_result += f"<p><strong>Creator:</strong> {metadata.get('uploader', 'Unknown')}</p>"
        html_result += f"<p><strong>Duration:</strong> {metadata.get('duration', 'Unknown')}</p>"
        html_result += f"<p><strong>Views:</strong> {metadata.get('view_count', 'Unknown')}</p>"
        html_result += f"<p><strong>Platform:</strong> {metadata.get('platform', 'Unknown')}</p>"

        tags = metadata.get('tags', [])
        if tags:
            html_result += f"<p><strong>Tags:</strong> {', '.join(tags[:5])}</p>"

    except Exception as e:
        error_msg = str(e)
        html_result += f"<p style='color: red;'>✗ Vimeo test failed: {error_msg}</p>"

        if "Failed to fetch android OAuth token" in error_msg:
            html_result += "<p style='color: orange;'>ℹ️ This error suggests Vimeo API changes. Cookies might need refresh.</p>"
        elif "HTTP Error 400" in error_msg:
            html_result += "<p style='color: orange;'>ℹ️ Bad request - cookies might be expired.</p>"

    html_result += "<hr><h3>Platform Configuration</h3>"
    html_result += f"<p>✓ Vimeo cookies configured in multi_platform_downloader.py</p>"
    html_result += f"<p>✓ Cookies file: {vimeo_cookies_file}</p>"
    html_result += f"<p>✓ Format preference: High quality (720p+) MP4</p>"

    return html_result

@app.route('/check_instagram_cookies')
def check_instagram_cookies():
    """Check Instagram cookies status and functionality"""
    import os

    html_result = "<h2>Instagram Cookies Status</h2>"

    # Check if Instagram cookies file exists
    instagram_cookies_exists = os.path.exists("cookies/instagram_cookies.txt")
    if instagram_cookies_exists:
        try:
            with open("cookies/instagram_cookies.txt", 'r') as f:
                content = f.read()
                has_sessionid = 'sessionid' in content
                has_csrftoken = 'csrftoken' in content
                has_ds_user_id = 'ds_user_id' in content
                lines_count = len(content.strip().split('\n'))

                html_result += f"<p style='color: green;'>✓ Instagram cookies file: EXISTS</p>"
                html_result += f"<p style='color: {'green' if has_sessionid else 'red'};'>{'✓' if has_sessionid else '✗'} Session ID present: {has_sessionid}</p>"
                html_result += f"<p style='color: {'green' if has_csrftoken else 'red'};'>{'✓' if has_csrftoken else '✗'} CSRF Token present: {has_csrftoken}</p>"
                html_result += f"<p style='color: {'green' if has_ds_user_id else 'red'};'>{'✓' if has_ds_user_id else '✗'} User ID present: {has_ds_user_id}</p>"
                html_result += f"<p>Total cookies: {lines_count - 4} entries</p>"  # Subtract header lines

        except Exception as e:
            html_result += f"<p style='color: red;'>✗ Error reading Instagram cookies: {e}</p>"
    else:
        html_result += f"<p style='color: red;'>✗ Instagram cookies file: NOT FOUND</p>"

    html_result += "<hr><h3>Instagram Authentication Test</h3>"

    # Test Instagram cookies with a simple metadata extraction
    try:
        from multi_platform_downloader import extract_platform_metadata
        test_url = "https://www.instagram.com/p/DNE4s7zpy58/"  # Sample Instagram URL
        metadata = extract_platform_metadata(test_url, 'instagram')
        html_result += f"<p style='color: green;'>✓ Instagram metadata extraction successful!</p>"
        html_result += f"<p>Title: {metadata.get('title', 'Unknown')}</p>"
        html_result += f"<p>Creator: {metadata.get('uploader', 'Unknown')}</p>"
    except Exception as e:
        html_result += f"<p style='color: red;'>✗ Instagram test failed: {e}</p>"
        if "Restricted Video" in str(e):
            html_result += f"<p style='color: orange;'>ℹ️ This might be due to geo-restrictions or expired cookies</p>"

    html_result += "<hr><h3>Multi-Platform Cookies Configuration</h3>"
    html_result += "<p>✓ Instagram: Using cookies/instagram_cookies.txt</p>"
    html_result += "<p>✓ Facebook: Using cookies/instagram_cookies.txt as fallback</p>" 
    html_result += "<p>✓ TikTok: Using cookies/instagram_cookies.txt as fallback</p>"

    return html_result

@app.route('/check_cookies')
def check_cookies():
    """Check cookies status and test functionality"""
    html_result = "<h2>Cookies Status Check</h2>"

    # Check fallback cookies
    fallback_exists = os.path.exists("cookies/fallback_cookies.txt")
    if fallback_exists:
        try:
            with open("cookies/fallback_cookies.txt", 'r') as f:
                content = f.read()
                login_info_present = 'LOGIN_INFO' in content
                html_result += f"<p style='color: green;'>✓ Fallback cookies file: EXISTS</p>"
                html_result += f"<p style='color: {'green' if login_info_present else 'red'};'>{'✓' if login_info_present else '?'} LOGIN_INFO present: {login_info_present}</p>"
                html_result += f"<p>File size: {len(content)} characters</p>"
        except Exception as e:
            html_result += f"<p style='color: red;'>✗ Error reading fallback cookies: {e}</p>"
    else:
        html_result += f"<p style='color: red;'>✗ Fallback cookies file: NOT FOUND</p>"

    # Check if user is logged in
    user_logged_in = 'access_token' in session
    html_result += f"<p style='color: {'green' if user_logged_in else 'orange'};'>{'✓' if user_logged_in else '?'} User logged in: {user_logged_in}</p>"

    if user_logged_in:
        user_id = session.get('user_id', 'unknown')
        user_cookies_file = f"db/{user_id}/cookies.txt"
        user_cookies_exist = os.path.exists(user_cookies_file)
        html_result += f"<p style='color: {'green' if user_cookies_exist else 'orange'};'>{'✓' if user_cookies_exist else '?'} User cookies exist: {user_cookies_exist}</p>"

        if user_cookies_exist:
            try:
                with open(user_cookies_file, 'r') as f:
                    user_content = f.read()
                    user_has_real_cookies = len(user_content) > 100 and 'LOGIN_INFO' in user_content
                    html_result += f"<p style='color: {'green' if user_has_real_cookies else 'orange'};'>{'✓' if user_has_real_cookies else '?'} User has real cookies: {user_has_real_cookies}</p>"
            except:
                html_result += f"<p style='color: red;'>✗ Error reading user cookies</p>"

    html_result += "<hr><h3>Test With Current Cookies</h3>"

    # Test metadata extraction with cookies
    try:
        from yt_metadata import extract_metadata
        test_url = "https://www.youtube.com/watch?v=jNQXAC9IVRw"
        metadata = extract_metadata(test_url)
        html_result += f"<p style='color: green;'>✓ Metadata extraction successful!</p>"
        html_result += f"<p>Title: {metadata.get('title', 'Unknown')}</p>"
        html_result += f"<p>Duration: {metadata.get('duration', 'Unknown')}</p>"
    except Exception as e:
        html_result += f"<p style='color: red;'>✗ Metadata extraction failed: {e}</p>"

    return html_result

@app.route('/platform_status')
def platform_status():
    """Get platform status and support information"""
    platforms_info = []

    # All platform configurations
    platform_configs = {
        'youtube': {
            'display_name': 'YouTube',
            'description': 'Videos, playlists, live streams',
            'supported': True,
            'icon': 'fab fa-youtube',
            'color': 'danger'
        },
        'instagram': {
            'display_name': 'Instagram', 
            'description': 'Reels, posts, stories, IGTV',
            'supported': True,
            'icon': 'fab fa-instagram',
            'color': 'warning'
        },
        'facebook': {
            'display_name': 'Facebook',
            'description': 'Public videos and posts',
            'supported': True,
            'icon': 'fab fa-facebook',
            'color': 'primary'
        },
        'twitter': {
            'display_name': 'Twitter/X',
            'description': 'Video tweets and embedded videos',
            'supported': True,
            'icon': 'fab fa-twitter',
            'color': 'info'
        },
        'tiktok': {
            'display_name': 'TikTok',
            'description': 'Videos and user content',
            'supported': True,
            'icon': 'fab fa-tiktok',
            'color': 'dark'
        },
        'vimeo': {
            'display_name': 'Vimeo',
            'description': 'Public and unlisted videos',
            'supported': True,
            'icon': 'fab fa-vimeo',
            'color': 'info'
        },
        'reddit': {
            'display_name': 'Reddit',
            'description': 'Video posts and embedded content',
            'supported': True,
            'icon': 'fab fa-reddit',
            'color': 'warning'
        },
        'twitch': {
            'display_name': 'Twitch',
            'description': 'Clips and VODs',
            'supported': True,
            'icon': 'fab fa-twitch',
            'color': 'purple'
        },
        'rumble': {
            'display_name': 'Rumble',
            'description': 'Videos and livestreams',
            'supported': True,
            'icon': 'fas fa-video',
            'color': 'success'
        },
        'dailymotion': {
            'display_name': 'Dailymotion',
            'description': 'Videos and playlists',
            'supported': True,
            'icon': 'fas fa-video',
            'color': 'primary'
        },
        'pinterest': {
            'display_name': 'Pinterest',
            'description': 'Video pins',
            'supported': True,
            'icon': 'fab fa-pinterest',
            'color': 'danger'
        },
        'snapchat': {
            'display_name': 'Snapchat',
            'description': 'Spotlight videos',
            'supported': True,
            'icon': 'fab fa-snapchat',
            'color': 'warning'
        },
        'direct_url': {
            'display_name': 'Direct URL',
            'description': 'Direct video file URLs (.mp4, .webm, .mkv, etc.)',
            'supported': True,
            'icon': 'fas fa-link',
            'color': 'success'
        }
    }

    for platform, config in platform_configs.items():
        platforms_info.append({
            'platform': platform,
            'display_name': config['display_name'],
            'description': config['description'],
            'supported': config['supported'],
            'status': 'Supported' if config['supported'] else 'Coming Soon',
            'icon': config['icon'],
            'color': config['color']
        })

    return jsonify({
        'platforms': platforms_info,
        'total_count': len(platforms_info),
        'supported_count': len([p for p in platforms_info if p['supported']]),
        'success': True
    })

@app.route('/test_comprehensive_platforms')
def test_comprehensive_platforms():
    """Test downloading 10 different high-quality videos"""
    # 10 diverse, high-quality test videos (popular, educational, music, etc.)
    test_urls = [
        'https://www.youtube.com/watch?v=jNQXAC9IVRw',  # Me at the zoo (first YouTube video)
        'https://www.youtube.com/watch?v=kffacxfIcf4',  # Charlie bit my finger  
        'https://www.youtube.com/watch?v=hFZFjoX2cGg',  # Educational content
        'https://www.youtube.com/watch?v=9bZkp7q19f0',  # Gangnam Style
        'https://www.youtube.com/watch?v=fJ9rUzIMcZQ',  # Bohemian Rhapsody
        'https://www.youtube.com/watch?v=L_jWHffIx5E',  # Smells Like Teen Spirit
        'https://www.youtube.com/watch?v=YQHsXMglC9A',  # Adele - Hello
        'https://www.youtube.com/watch?v=RgKAFK5djSk',  # Wiz Khalifa - See You Again
        'https://www.youtube.com/watch?v=CevxZvSJLk8',  # Katy Perry - Roar
        'https://www.youtube.com/watch?v=pRpeEdMmmQ0'   # Shakira - Whenever, Wherever
    ]

    from yt_uploader import test_video_download

    try:
        results = test_video_download(test_urls, "high_quality_test")

        html_results = "<h2>High Quality Video Download Test Results</h2>"
        html_results += f"<p><strong>Total Videos Tested:</strong> {len(test_urls)}</p>"

        success_count = 0
        for i, result in enumerate(results):
            url = test_urls[i]
            video_num = i + 1

            if result['success']:
                success_count += 1
                html_results += f"<div class='alert alert-success'>"
                html_results += f"<h5>✓ Video {video_num}: SUCCESS</h5>"
                html_results += f"<p><strong>Title:</strong> {result.get('title', 'N/A')}</p>"
                html_results += f"<p><strong>Quality:</strong> {result.get('quality', 'N/A')}</p>"
                html_results += f"<p><strong>File Size:</strong> {result.get('file_size', 'N/A')}</p>"
                html_results += f"<p><strong>Duration:</strong> {result.get('duration', 'N/A')}</p>"
                html_results += f"<small><strong>URL:</strong> {url}</small>"
                html_results += f"</div>"
            else:
                html_results += f"<div class='alert alert-danger'>"
                html_results += f"<h5>✗ Video {video_num}: FAILED</h5>"
                html_results += f"<p><strong>Error:</strong> {result.get('error', 'Unknown error')}</p>"
                html_results += f"<small><strong>URL:</strong> {url}</small>"
                html_results += f"</div>"

        # Final score
        score = f"{success_count}/{len(test_urls)}"
        color = "success" if success_count == len(test_urls) else "warning" if success_count >= 8 else "danger"

        html_results += f"<div class='alert alert-{color} text-center'>"
        html_results += f"<h3>Final Score: {score}</h3>"
        if success_count == len(test_urls):
            html_results += f"<p>🎉 Perfect! All videos downloaded successfully in high quality!</p>"
        elif success_count >= 8:
            html_results += f"<p>⚠️ Most videos downloaded successfully. Some issues to investigate.</p>"
        else:
            html_results += f"<p>❌ Multiple failures detected. System needs attention.</p>"
        html_results += f"</div>"

        return html_results

    except Exception as e:
        return f"<h2>Test Error</h2><p style='color: red;'>{str(e)}</p>"

@app.route('/detect_platform', methods=['POST'])
def detect_platform():
    """Detect platform from URL"""
    url = request.form.get('url')
    if not url:
        return jsonify({'error': 'No URL provided'}), 400

    platform = get_platform_from_url(url)
    supported = is_platform_supported(url)
    display_name = get_platform_display_name(platform)

    return jsonify({
        'platform': platform,
        'display_name': display_name,
        'supported': supported,
        'url': url
    })

@app.route('/supported_platforms')
def supported_platforms():
    """Get list of supported platforms"""
    platforms = get_supported_platforms()
    platform_info = []

    for platform in platforms:
        platform_info.append({
            'id': platform,
            'name': get_platform_display_name(platform),
            'description': f'Download videos from {get_platform_display_name(platform)}'
        })

    return jsonify({
        'platforms': platform_info,
        'total': len(platforms)
    })

@app.route('/platforms')
def platforms():
    """Show supported platforms page"""
    return render_template('platforms.html')

@app.route('/privacy')
def privacy():
    """Show privacy policy page"""
    return render_template('privacy.html')

@app.route('/test_quality_settings')
def test_quality_settings():
    """Test quality settings for all platforms"""
    from multi_platform_downloader import get_platform_config, get_supported_platforms, get_platform_display_name

    platforms = get_supported_platforms()
    quality_info = []

    for platform in platforms:
        config = get_platform_config(platform)
        quality_info.append({
            'platform': platform,
            'display_name': get_platform_display_name(platform),
            'format_selector': config.get('format', 'Not configured'),
            'supports_720p': 'height>=720' in config.get('format', ''),
            'max_quality': '1080p' if 'height<=1080' in config.get('format', '') else 'Best available'
        })

    html_result = "<h2>Video Quality Settings Test</h2>"
    html_result += "<p class='lead'>All platforms are configured for minimum 720p quality downloads:</p>"
    html_result += "<div class='table-responsive'><table class='table table-striped'>"
    html_result += "<thead><tr><th>Platform</th><th>720p Minimum</th><th>Max Quality</th><th>Format Selector</th></tr></thead><tbody>"

    for info in quality_info:
        status_color = 'success' if info['supports_720p'] else 'danger'
        status_text = '✓ Yes' if info['supports_720p'] else '✗ No'

        html_result += f"<tr>"
        html_result += f"<td><strong>{info['display_name']}</strong></td>"
        html_result += f"<td><span class='badge bg-{status_color}'>{status_text}</span></td>"
        html_result += f"<td>{info['max_quality']}</td>"
        html_result += f"<td><code>{info['format_selector']}</code></td>"
        html_result += f"</tr>"

    html_result += "</tbody></table></div>"

    # Summary
    total_platforms = len(quality_info)
    hd_platforms = sum(1 for info in quality_info if info['supports_720p'])

    html_result += f"<div class='alert alert-success mt-4'>"
    html_result += f"<h5>✓ Quality Assurance Summary</h5>"
    html_result += f"<p><strong>{hd_platforms}/{total_platforms}</strong> platforms configured for minimum 720p quality</p>"
    html_result += f"<p><strong>Quality Priority:</strong> 1080p HD → 720p HD → Best Available</p>"
    html_result += f"<p><strong>Formats:</strong> MP4 preferred, WebM fallback</p>"
    html_result += f"</div>"

    return html_result

@app.route('/test_working_platforms')
def test_working_platforms():
    """Test reliable platforms with real working URLs"""
    from focused_testing import test_reliable_platforms

    try:
        results = test_reliable_platforms()

        html_result = "<h2>🧪 Comprehensive Platform Test Results</h2>"
        html_result += f"<div class='alert alert-info'><strong>Summary:</strong> {results['summary']}</div>"

        # Success rate indicator
        success_rate = float(results['success_rate'].replace('%', ''))
        if success_rate >= 80:
            alert_type = 'success'
            emoji = '✅'
        elif success_rate >= 60:
            alert_type = 'warning' 
            emoji = '⚠️'
        else:
            alert_type = 'danger'
            emoji = '❌'

        html_result += f"<div class='alert alert-{alert_type} text-center'>"  
        html_result += f"<h4>{emoji} Overall Success Rate: {results['success_rate']}</h4>"
        html_result += f"</div>"

        # Platform coverage table
        html_result += "<h4>📊 Platform Coverage</h4>"
        html_result += "<table class='table table-striped'>"
        html_result += "<thead><tr><th>Platform</th><th>Tests</th><th>Successful</th><th>Rate</th></tr></thead><tbody>"

        for platform, stats in results['platform_coverage'].items():
            rate = (stats['successful'] / stats['tested']) * 100 if stats['tested'] > 0 else 0
            rate_color = 'success' if rate >= 80 else 'warning' if rate >= 50 else 'danger'
            html_result += f"<tr>"
            html_result += f"<td><strong>{get_platform_display_name(platform)}</strong></td>"
            html_result += f"<td>{stats['tested']}</td>"
            html_result += f"<td>{stats['successful']}</td>"
            html_result += f"<td><span class='badge bg-{rate_color}'>{rate:.1f}%</span></td>"
            html_result += f"</tr>"

        html_result += "</tbody></table>"

        # Detailed test results
        html_result += "<h4>🔍 Detailed Test Results</h4>"

        for test_result in results['test_results']:
            status = test_result['status']
            if status == 'success':
                card_class = 'border-success'
                icon = '✅'
                bg_class = 'bg-success bg-opacity-10'
            elif status == 'expected_failure':
                card_class = 'border-warning'
                icon = '⚠️'
                bg_class = 'bg-warning bg-opacity-10'
            else:
                card_class = 'border-danger'
                icon = '❌'
                bg_class = 'bg-danger bg-opacity-10'

            html_result += f"<div class='card {card_class} mb-3'>"
            html_result += f"<div class='card-header {bg_class}'>"
            html_result += f"<h6>{icon} Test #{test_result['test_number']}: {test_result['platform_display']} - {test_result['test_type'].replace('_', ' ').title()}</h6>"
            html_result += f"</div><div class='card-body'>"

            if status == 'success':
                metadata = test_result['metadata']
                html_result += f"<p><strong>Title:</strong> {metadata.get('title', 'N/A')}</p>"
                html_result += f"<p><strong>Creator:</strong> {metadata.get('uploader', 'N/A')}</p>"
                html_result += f"<p><strong>Duration:</strong> {metadata.get('duration', 'N/A')}</p>"
                html_result += f"<p><strong>Views:</strong> {metadata.get('view_count', 'N/A')}</p>"
                html_result += f"<p><strong>Tags:</strong> {metadata.get('tags_count', 0)} found</p>"
                html_result += f"<p><strong>Extraction Time:</strong> {test_result.get('extraction_time', 'N/A')}</p>"
            else:
                html_result += f"<p><strong>Error:</strong> {test_result.get('error', 'Unknown error')}</p>"
                if test_result.get('error_category'):
                    html_result += f"<p><strong>Error Type:</strong> {test_result['error_category'].replace('_', ' ').title()}</p>"

            if test_result.get('notes'):
                html_result += f"<p><strong>Notes:</strong> {'; '.join(test_result['notes'])}</p>"

            html_result += f"<small class='text-muted'>URL: {test_result['url']}</small>"
            html_result += f"</div></div>"

        return html_result

    except Exception as e:
        return f"<h2>Test Error</h2><p style='color: red;'>Failed to run comprehensive test: {str(e)}</p>"

@app.route('/test_quick_metadata')
def test_quick_metadata():
    """Quick metadata test for reliable platforms"""
    from comprehensive_testing import quick_metadata_test

    try:
        results = quick_metadata_test()

        html_result = "<h2>⚡ Quick Metadata Test</h2>"
        html_result += "<p class='lead'>Testing metadata extraction from reliable platforms:</p>"

        success_count = len([r for r in results if r['status'] == 'success'])
        total_count = len(results)

        html_result += f"<div class='alert alert-info'>Success Rate: {success_count}/{total_count} platforms</div>"

        for result in results:
            status = result['status']
            if status == 'success':
                html_result += f"<div class='card border-success mb-3'>"
                html_result += f"<div class='card-header bg-success bg-opacity-10'>"
                html_result += f"<h6>✅ {result['platform']} - Success</h6>"
                html_result += f"</div><div class='card-body'>"
                html_result += f"<p><strong>Title:</strong> {result.get('title', 'N/A')}</p>"
                html_result += f"<p><strong>Creator:</strong> {result.get('uploader', 'N/A')}</p>"
                html_result += f"<p><strong>Duration:</strong> {result.get('duration', 'N/A')}</p>"
                html_result += f"<p><strong>Extraction Time:</strong> {result.get('extraction_time', 'N/A')}</p>"
            else:
                html_result += f"<div class='card border-danger mb-3'>"
                html_result += f"<div class='card-header bg-danger bg-opacity-10'>"
                html_result += f"<h6>❌ {result['platform']} - Failed</h6>"
                html_result += f"</div><div class='card-body'>"
                html_result += f"<p><strong>Error:</strong> {result.get('error', 'Unknown error')}</p>"

            html_result += f"<small class='text-muted'>URL: {result['url']}</small>"
            html_result += f"</div></div>"

        return html_result

    except Exception as e:
        return f"<h2>Test Error</h2><p style='color: red;'>Failed to run quick test: {str(e)}</p>"

@app.route('/test_platform_detection')
def test_platform_detection():
    """Test platform detection capabilities"""
    from comprehensive_testing import platform_capabilities_test

    try:
        results = platform_capabilities_test()

        html_result = "<h2>🎯 Platform Detection Test</h2>"
        html_result += f"<p class='lead'>Testing URL platform detection and support status:</p>"

        detection_results = results['detection_tests']
        correct_count = len([r for r in detection_results if r['correct']])
        total_count = len(detection_results)

        html_result += f"<div class='alert alert-info'>"
        html_result += f"<strong>Detection Accuracy:</strong> {correct_count}/{total_count} correct"
        html_result += f"<br><strong>Supported Platforms:</strong> {results['total_platforms']} platforms"
        html_result += f"</div>"

        html_result += "<table class='table table-striped'>"
        html_result += "<thead><tr><th>Test URL</th><th>Expected</th><th>Detected</th><th>Correct</th><th>Supported</th></tr></thead><tbody>"

        for result in detection_results:
            correct_icon = '✅' if result['correct'] else '❌'
            support_icon = '✅' if result['supported'] else '❌'
            row_class = 'table-success' if result['correct'] and result['supported'] else 'table-warning' if result['correct'] else 'table-danger'

            html_result += f"<tr class='{row_class}'>"
            html_result += f"<td><code>{result['url']}</code></td>"
            html_result += f"<td><strong>{result['expected']}</strong></td>"
            html_result += f"<td><strong>{result['detected']}</strong> ({result['display_name']})</td>"
            html_result += f"<td class='text-center'>{correct_icon}</td>"
            html_result += f"<td class='text-center'>{support_icon}</td>"
            html_result += f"</tr>"

        html_result += "</tbody></table>"

        # Supported platforms list
        html_result += "<h4>📋 Supported Platforms</h4>"
        html_result += "<div class='row'>"

        for i, platform in enumerate(results['supported_platforms']):
            if i % 3 == 0 and i > 0:
                html_result += "</div><div class='row'>"

            html_result += f"<div class='col-md-4 mb-2'>"
            html_result += f"<span class='badge bg-primary'>{get_platform_display_name(platform)}</span>"
            html_result += f"</div>"

        html_result += "</div>"

        return html_result

    except Exception as e:
        return f"<h2>Test Error</h2><p style='color: red;'>Failed to run detection test: {str(e)}</p>"

# Static Pages Routes
@app.route('/about')
def about():
    """About page"""
    with open('pages/about.md', 'r') as f:
        content = markdown.markdown(f.read())
    return render_template('static_page.html', title='About UpDownVid', content=content, page='about')

@app.route('/tos')
def tos():
    """Terms of Service page"""
    with open('pages/tos.md', 'r') as f:
        content = markdown.markdown(f.read())
    return render_template('static_page.html', title='Terms of Service', content=content, page='tos')

@app.route('/copyright')
def copyright_policy():
    """Copyright/DMCA Policy page"""
    with open('pages/copyright.md', 'r') as f:
        content = markdown.markdown(f.read())
    return render_template('static_page.html', title='Copyright & DMCA Policy', content=content, page='copyright')

@app.route('/faq')
def faq():
    """FAQ page"""
    with open('pages/faq.md', 'r') as f:
        content = markdown.markdown(f.read())
    return render_template('static_page.html', title='Frequently Asked Questions', content=content, page='faq')

@app.route('/contact')
def contact():
    """Contact page"""
    with open('pages/contact.md', 'r') as f:
        content = markdown.markdown(f.read())
    return render_template('static_page.html', title='Contact Us', content=content, page='contact')

@app.route('/submit_contact', methods=['POST'])
def submit_contact():
    """Handle contact form submission"""
    try:
        # Check if SMTP is configured
        smtp_enabled = os.environ.get('ENABLE_CONTACT_FORM', 'false').lower() == 'true'
        if not smtp_enabled:
            return jsonify({'error': 'Contact form is currently disabled. Please email us directly.'}), 503
        
        # Get form data
        name = request.form.get('name')
        email = request.form.get('email')
        subject = request.form.get('subject')
        message = request.form.get('message')
        
        if not all([name, email, subject, message]):
            return jsonify({'error': 'All fields are required'}), 400
        
        # Send email via SMTP
        smtp_host = os.environ.get('SMTP_HOST')
        smtp_port = int(os.environ.get('SMTP_PORT', 587))
        smtp_user = os.environ.get('SMTP_USER')
        smtp_pass = os.environ.get('SMTP_PASS')
        smtp_from = os.environ.get('SMTP_FROM')
        contact_email = os.environ.get('CONTACT_EMAIL', 'support@updownvid.com')
        
        if not all([smtp_host, smtp_user, smtp_pass]):
            return jsonify({'error': 'SMTP not configured'}), 500
        
        # Create message
        msg = MIMEMultipart()
        msg['From'] = smtp_from
        msg['To'] = contact_email
        msg['Subject'] = f"[UpDownVid Contact] {subject} - {name}"
        
        body = f"""
New contact form submission:

From: {name} <{email}>
Subject: {subject}

Message:
{message}

---
Sent via UpDownVid Contact Form
"""
        msg.attach(MIMEText(body, 'plain'))
        
        # Send email
        with smtplib.SMTP(smtp_host, smtp_port) as server:
            server.starttls()
            server.login(smtp_user, smtp_pass)
            server.send_message(msg)
        
        return jsonify({
            'success': True,
            'message': 'Thank you for your message! We will respond within 48-72 hours.'
        })
        
    except Exception as e:
        logging.error(f"Contact form error: {e}")
        return jsonify({'error': 'Failed to send message. Please email us directly.'}), 500

# YouTube Channel Automation Routes
@app.route('/automation')
def automation():
    """Channel automation page"""
    # Check if user is authenticated for upload functionality
    if 'access_token' not in session:
        flash('Please connect your Google account to use automation features.', 'error')
        return redirect(url_for('accounts'))
    
    return render_template('automation.html')

@app.route('/automation/get_settings')
def get_automation_settings():
    """Get current automation settings"""
    try:
        user_id = get_user_id()
        import asyncio
        from mongo import get_user_settings
        settings = asyncio.run(get_user_settings(user_id))
        return jsonify(settings)
    except Exception as e:
        logging.error(f"Error getting automation settings: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/automation/save_settings', methods=['POST'])
def save_automation_settings():
    """Save automation settings"""
    try:
        user_id = get_user_id()
        settings = request.get_json()
        
        import asyncio
        from mongo import save_user_settings
        asyncio.run(save_user_settings(user_id, settings))
        
        return jsonify({'success': True})
    except Exception as e:
        logging.error(f"Error saving automation settings: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/automation/get_channels')
def get_automation_channels():
    """Get monitored channels"""
    try:
        user_id = get_user_id()
        import asyncio
        from mongo import get_user_channels
        data = asyncio.run(get_user_channels(user_id))
        return jsonify(data)
    except Exception as e:
        logging.error(f"Error getting automation channels: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/automation/fetch_channel_info', methods=['POST'])
def fetch_channel_info():
    """Fetch channel information using YouTube API v3"""
    try:
        # Validate request data
        try:
            data = request.get_json()
        except Exception as json_error:
            logging.error(f"JSON parsing error: {json_error}")
            return jsonify({'error': 'Invalid JSON data'}), 400
            
        if not data:
            return jsonify({'error': 'No data provided'}), 400
            
        channel_url = data.get('channel_url')
        if not channel_url:
            return jsonify({'error': 'Channel URL is required'}), 400
        
        # Validate channel URL format
        if not ('youtube.com' in channel_url or 'youtu.be' in channel_url):
            return jsonify({'error': 'Please provide a valid YouTube channel URL'}), 400
        
        # Get user's API key from settings
        try:
            user_id = get_user_id()
        except Exception as auth_error:
            logging.error(f"Authentication error: {auth_error}")
            return jsonify({'error': 'Authentication required'}), 401
            
        settings_file = f"db/{user_id}/settings.json"
        api_key = None
        
        if os.path.exists(settings_file):
            try:
                with open(settings_file, 'r', encoding='utf-8') as f:
                    settings = json.load(f)
                    api_key = settings.get('api_key')
            except Exception as settings_error:
                logging.error(f"Error reading settings: {settings_error}")
        
        # Extract channel info using YouTube API v3
        try:
            from auth_helper import get_channel_info_with_videos_api_v3
            channel_info = get_channel_info_with_videos_api_v3(channel_url, api_key)
            
            return jsonify({
                'success': True,
                'channel_id': channel_info['channel_id'],
                'name': channel_info['name'],
                'logo_url': channel_info['logo_url'],
                'subscriber_count': channel_info.get('subscribers', 'Unknown'),
                'total_videos': channel_info.get('video_count', 0),
                'latest_videos': channel_info.get('latest_videos', [])
            })
            
        except Exception as api_error:
            api_error_msg = str(api_error)
            logging.error(f"API error: {api_error_msg}")
            
            # Provide more specific error messages
            if 'Could not extract channel ID' in api_error_msg:
                return jsonify({'error': 'Invalid YouTube channel URL format. Please use a valid channel URL.'}), 400
            elif 'API key not found' in api_error_msg:
                return jsonify({'error': 'YouTube API key not configured. Please add your API key in Global Settings.'}), 500
            elif 'Channel not found' in api_error_msg:
                return jsonify({'error': 'Channel not found or may be private/deleted.'}), 404
            elif 'quota' in api_error_msg.lower():
                return jsonify({'error': 'YouTube API quota exceeded. Please try again later.'}), 429
            elif 'forbidden' in api_error_msg.lower():
                return jsonify({'error': 'Access forbidden. Please check your API key permissions.'}), 403
            else:
                return jsonify({'error': f'Failed to fetch channel information: {api_error_msg}'}), 500
                
    except Exception as e:
        error_msg = str(e)
        logging.error(f"Unexpected error fetching channel info: {error_msg}")
        return jsonify({'error': 'An unexpected error occurred. Please try again.'}), 500

@app.route('/automation/fetch_latest_videos', methods=['GET'])
def fetch_latest_videos():
    """Fetch latest videos from a channel using YouTube API v3"""
    try:
        channel_id = request.args.get('channel_id')
        if not channel_id:
            return jsonify({'error': 'Channel ID is required'}), 400
        
        # Get user's API key from settings
        user_id = get_user_id()
        settings_file = f"db/{user_id}/settings.json"
        api_key = None
        
        if os.path.exists(settings_file):
            with open(settings_file, 'r') as f:
                settings = json.load(f)
                api_key = settings.get('api_key')
        
        from auth_helper import get_channel_latest_videos_api_v3
        videos = get_channel_latest_videos_api_v3(channel_id, api_key, max_results=5)
        return jsonify({'success': True, 'videos': videos})
        
    except Exception as e:
        logging.error(f"Error fetching latest videos: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/automation/add_channel', methods=['POST'])
def add_automation_channel():
    """Add channel for monitoring"""
    try:
        user_id = get_user_id()
        data = request.get_json()
        channel_info = data.get('channel_info')
        
        if not channel_info:
            return jsonify({'error': 'Channel info is required'}), 400
        
        import asyncio
        from mongo import get_user_channels, save_user_channels
        
        # Load existing channels
        channels_data = asyncio.run(get_user_channels(user_id))
        
        # Check if channel already exists
        for existing_channel in channels_data['channels']:
            if existing_channel['channel_id'] == channel_info['channel_id']:
                return jsonify({'error': 'Channel is already being monitored'}), 400
        
        # Add monitor interval and quality defaults
        channel_info['monitor_interval'] = 10
        channel_info['quality'] = '1080p'
        channel_info['last_checked'] = None
        channel_info['last_video_count'] = channel_info.get('total_videos', 0)
        
        # Add new channel
        channels_data['channels'].append(channel_info)
        
        asyncio.run(save_user_channels(user_id, channels_data))
        
        return jsonify({'success': True, 'channel': channel_info})
    except Exception as e:
        logging.error(f"Error adding automation channel: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/automation/remove_channel', methods=['POST'])
def remove_automation_channel():
    """Remove channel from monitoring"""
    try:
        user_id = get_user_id()
        channel_id = request.get_json().get('channel_id')
        
        if not channel_id:
            return jsonify({'error': 'Channel ID is required'}), 400
        
        import asyncio
        from mongo import get_user_channels, save_user_channels
        
        data = asyncio.run(get_user_channels(user_id))
        data['channels'] = [ch for ch in data['channels'] if ch['channel_id'] != channel_id]
        asyncio.run(save_user_channels(user_id, data))
        
        return jsonify({'success': True})
    except Exception as e:
        logging.error(f"Error removing automation channel: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/automation/get_logs')
def get_automation_logs():
    """Get automation logs"""
    try:
        # Check if user is authenticated
        if 'access_token' not in session:
            return jsonify({'logs': [], 'service_status': False, 'error': 'Not authenticated'})
        
        # Try to get user info to validate token
        try:
            user_info = get_user_info(session['access_token'])
            user_id = user_info['email'].replace('@', '_').replace('.', '_')
        except Exception as auth_error:
            logging.warning(f"Authentication error: {auth_error}")
            if 'refresh_token' in session:
                try:
                    new_access_token = refresh_access_token(session['refresh_token'])
                    session['access_token'] = new_access_token
                    user_info = get_user_info(new_access_token)
                    user_id = user_info['email'].replace('@', '_').replace('.', '_')
                    logging.info("Successfully refreshed access token")
                except Exception as refresh_error:
                    logging.error(f"Token refresh failed: {refresh_error}")
                    return jsonify({'logs': [], 'service_status': False, 'error': 'Authentication expired'})
            else:
                return jsonify({'logs': [], 'service_status': False, 'error': 'Authentication expired'})
        
        import asyncio
        from mongo import get_automation_logs as get_logs_mongo
        logs_data = asyncio.run(get_logs_mongo(user_id))
        
        # Ensure logs are in the correct format
        logs = logs_data.get('logs', [])
        if not isinstance(logs, list):
            logs = []
        
        # Return last 100 logs
        filtered_logs = []
        for log in logs[-100:]:
            if isinstance(log, dict) and 'timestamp' in log and 'message' in log:
                filtered_logs.append({
                    'timestamp': log.get('timestamp', 0),
                    'type': log.get('type', 'info'),
                    'message': str(log.get('message', ''))
                })
        
        return jsonify({
            'logs': filtered_logs,
            'service_status': bool(logs_data.get('service_status', False))
        })
            
    except Exception as e:
        logging.error(f"Error getting automation logs: {e}")
        return jsonify({'logs': [], 'service_status': False, 'error': 'Server error occurred'}), 500

@app.route('/automation/clear_logs', methods=['POST'])
def clear_automation_logs():
    """Clear automation logs"""
    try:
        user_id = get_user_id()
        
        import asyncio
        from mongo import save_automation_logs
        logs_data = {'logs': [], 'service_status': False}
        asyncio.run(save_automation_logs(user_id, logs_data))
        
        return jsonify({'success': True})
    except Exception as e:
        logging.error(f"Error clearing automation logs: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/automation/start_monitoring', methods=['POST'])
def start_automation_monitoring():
    """Start the automation monitoring service"""
    try:
        user_id = get_user_id()
        
        # Start monitoring service in background thread
        thread = threading.Thread(target=automation_monitor_worker, args=(user_id,))
        thread.daemon = True
        thread.start()
        
        # Update service status
        add_automation_log(user_id, 'success', 'Monitoring service started')
        
        return jsonify({'success': True})
    except Exception as e:
        logging.error(f"Error starting automation monitoring: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/automation/stop_monitoring', methods=['POST'])
def stop_automation_monitoring():
    """Stop the automation monitoring service"""
    try:
        user_id = get_user_id()
        
        # Set stop flag (in real implementation, you'd use a proper mechanism)
        set_automation_service_status(user_id, False)
        add_automation_log(user_id, 'info', 'Monitoring service stopped by user')
        
        return jsonify({'success': True})
    except Exception as e:
        logging.error(f"Error stopping automation monitoring: {e}")
        return jsonify({'error': str(e)}), 500

def get_user_id():
    """Get current user email from session (used as directory identifier)"""
    if 'access_token' not in session:
        raise Exception('User not authenticated')
    
    try:
        user_info = get_user_info(session['access_token'])
        return user_info['email'].replace('@', '_').replace('.', '_')  # Use email as directory name
    except Exception:
        # Try to refresh token if available
        if 'refresh_token' in session:
            try:
                new_access_token = refresh_access_token(session['refresh_token'])
                session['access_token'] = new_access_token
                user_info = get_user_info(new_access_token)
                return user_info['email'].replace('@', '_').replace('.', '_')  # Use email as directory name
            except Exception:
                raise Exception('Authentication expired, please login again')
        else:
            raise Exception('Authentication expired, please login again')

def get_stored_user_tokens(user_email_dir):
    """Get stored access tokens for background automation"""
    try:
        import asyncio
        from mongo import get_user_tokens
        tokens = asyncio.run(get_user_tokens(user_email_dir))
        if tokens:
            return tokens.get('access_token'), tokens.get('refresh_token')
        return None, None
    except Exception:
        return None, None

def store_user_tokens(user_email_dir, access_token, refresh_token):
    """Store user tokens for background automation"""
    try:
        import asyncio
        from mongo import store_user_tokens as mongo_store
        asyncio.run(mongo_store(user_email_dir, access_token, refresh_token))
    except Exception as e:
        logging.error(f"Error storing user tokens: {e}")

def process_video_for_automation(user_id, video_url, video_title, video_metadata):
    """Process video download and upload for automation"""
    try:
        # Get stored user tokens
        access_token, refresh_token = get_stored_user_tokens(user_id)
        
        if not access_token:
            raise Exception("No stored access token for user")
        
        # Try to refresh token if needed
        try:
            # Test if token is still valid
            get_user_info(access_token)
        except Exception:
            if refresh_token:
                try:
                    access_token = refresh_access_token(refresh_token)
                    store_user_tokens(user_id, access_token, refresh_token)
                except Exception:
                    raise Exception("Token refresh failed")
            else:
                raise Exception("No valid tokens available")
        
        # Download video using multi_platform_downloader
        from multi_platform_downloader import download_from_platform, get_platform_from_url
        
        platform = get_platform_from_url(video_url)
        user_dir = f"db/{user_id}"
        download_path = f"{user_dir}/downloads"
        os.makedirs(download_path, exist_ok=True)
        
        # Download the video
        downloaded_file = download_from_platform(video_url, download_path, platform)
        
        if not downloaded_file or not os.path.exists(downloaded_file):
            raise Exception("Video download failed")
        
        # Upload to YouTube using yt_uploader
        from yt_uploader import upload_to_youtube
        
        # Create upload metadata
        upload_title = video_title
        upload_description = f"Original video from {platform}\n\n{video_metadata.get('description', '')}"
        upload_tags = video_metadata.get('tags', [])
        upload_privacy = 'public'
        
        # Create dummy progress tracking for upload
        upload_id = f"auto_{user_id}_{int(time.time())}"
        progress_data = {upload_id: {'status': 'uploading', 'progress': 0}}
        
        # Upload to YouTube
        youtube_url = upload_to_youtube(
            downloaded_file,
            access_token,
            upload_title,
            upload_description,
            upload_tags,
            upload_privacy,
            upload_id,
            progress_data
        )
        
        # Clean up downloaded file
        try:
            if os.path.exists(downloaded_file):
                os.remove(downloaded_file)
        except Exception:
            pass
        
        return youtube_url
        
    except Exception as e:
        logging.error(f"Error processing video for automation: {e}")
        raise e

def get_channel_info_hybrid(channel_url):
    """Extract YouTube channel information using YouTube API v3 + RSS"""
    import re
    import feedparser
    
    # Extract channel ID from URL
    channel_id = None
    
    if 'youtube.com/@' in channel_url:
        # Handle @username format - need to resolve to channel ID via scraping
        response = requests.get(channel_url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'})
        response.raise_for_status()
        
        # Extract channel ID from page
        channel_id_match = re.search(r'"channelId":"([^"]+)"', response.text)
        if channel_id_match:
            channel_id = channel_id_match.group(1)
        else:
            raise Exception('Could not extract channel ID from @username URL')
    
    elif 'youtube.com/channel/' in channel_url:
        # Direct channel ID extraction
        channel_id = channel_url.split('/channel/')[-1].split('?')[0]
    
    elif 'youtube.com/c/' in channel_url or 'youtube.com/user/' in channel_url:
        # Handle custom URLs by scraping
        response = requests.get(channel_url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'})
        response.raise_for_status()
        
        channel_id_match = re.search(r'"channelId":"([^"]+)"', response.text)
        if channel_id_match:
            channel_id = channel_id_match.group(1)
        else:
            raise Exception('Could not extract channel ID from custom URL')
    
    elif channel_url.startswith('UC') and len(channel_url) == 24:
        # Direct channel ID
        channel_id = channel_url
        channel_url = f"https://www.youtube.com/channel/{channel_id}"
    
    else:
        raise Exception('Invalid YouTube channel URL format')
    
    if not channel_id:
        raise Exception('Could not extract channel ID')
    
    # Use YouTube API v3 to get channel information
    try:
        # Get API key from environment
        api_key = os.environ.get('YOUTUBE_API_KEY')
        if not api_key:
            raise Exception('YouTube API key not found in environment variables')
        
        # Fetch channel details using YouTube API v3
        api_url = 'https://www.googleapis.com/youtube/v3/channels'
        params = {
            'part': 'snippet,statistics',
            'id': channel_id,
            'key': api_key
        }
        
        response = requests.get(api_url, params=params)
        response.raise_for_status()
        
        data = response.json()
        
        if not data.get('items'):
            raise Exception('Channel not found or API request failed')
        
        channel_info = data['items'][0]
        snippet = channel_info['snippet']
        statistics = channel_info['statistics']
        
        # Extract channel details
        name = snippet.get('title', 'Unknown Channel')
        logo_url = snippet.get('thumbnails', {}).get('high', {}).get('url', 
                    f"https://yt3.ggpht.com/a/default-user=s800-c-k-c0x00ffffff-no-rj")
        
        # Format subscriber count
        subscriber_count = int(statistics.get('subscriberCount', 0))
        if subscriber_count >= 1_000_000:
            subscribers = f"{subscriber_count / 1_000_000:.1f}M subscribers"
        elif subscriber_count >= 1_000:
            subscribers = f"{subscriber_count / 1_000:.1f}K subscribers"
        else:
            subscribers = f"{subscriber_count} subscribers"
        
        # Format video count
        video_count = statistics.get('videoCount', 0)
        
        logging.info(f"Successfully fetched channel info via YouTube API: {name}")
        
    except Exception as api_error:
        logging.warning(f"YouTube API failed: {api_error}, falling back to default values")
        name = "Unknown Channel"
        logo_url = f"https://yt3.ggpht.com/a/default-user=s800-c-k-c0x00ffffff-no-rj"
        subscribers = "Unknown"
        video_count = "Unknown"
    
    # RSS logic for latest videos
    latest_videos = []
    try:
        rss_url = f"https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}"
        feed = feedparser.parse(rss_url)
        
        if feed.entries:
            for entry in feed.entries[:3]:  # Top 3 videos
                latest_videos.append({
                    'title': entry.get('title', 'Unknown Title'),
                    'url': entry.get('link', ''),
                    'published': entry.get('published', 'Unknown Date'),
                    'thumbnail': f"https://i.ytimg.com/vi/{entry.yt_videoid}/mqdefault.jpg" if hasattr(entry, 'yt_videoid') else ''
                })
        else:
            latest_videos = [{'title': 'No videos found', 'url': '', 'published': '', 'thumbnail': ''}]
            
    except Exception as rss_error:
        logging.warning(f"RSS fetch failed: {rss_error}")
        latest_videos = [{'title': 'Unable to get videos', 'url': '', 'published': '', 'thumbnail': ''}]
    
    return {
        'channel_id': channel_id,
        'name': name,
        'logo_url': logo_url,
        'subscribers': subscribers,
        'video_count': video_count,
        'latest_videos': latest_videos
    }

def get_channel_latest_videos(channel_id, access_token=None, max_results=3):
    """Get latest videos from a channel using YouTube API v3"""
    try:
        # Try using OAuth access token first if provided
        if access_token:
            from auth_helper import get_youtube_api_service
            youtube = get_youtube_api_service(access_token)
            
            # Get latest videos using OAuth
            search_response = youtube.search().list(
                channelId=channel_id,
                part='snippet',
                order='date',
                type='video',
                maxResults=max_results
            ).execute()
            
            videos = []
            for item in search_response['items']:
                videos.append({
                    'video_id': item['id']['videoId'],
                    'title': item['snippet']['title'],
                    'published': item['snippet']['publishedAt'],
                    'thumbnail': item['snippet']['thumbnails']['medium']['url'],
                    'url': f"https://www.youtube.com/watch?v={item['id']['videoId']}"
                })
            
            logging.info(f"Successfully fetched {len(videos)} videos via YouTube API (OAuth)")
            return videos
        
        else:
            # Use API key method
            api_key = os.environ.get('YOUTUBE_API_KEY')
            if not api_key:
                raise Exception('YouTube API key not found')
            
            # Fetch videos using YouTube API v3 with API key
            api_url = 'https://www.googleapis.com/youtube/v3/search'
            params = {
                'part': 'snippet',
                'channelId': channel_id,
                'order': 'date',
                'type': 'video',
                'maxResults': max_results,
                'key': api_key
            }
            
            response = requests.get(api_url, params=params)
            response.raise_for_status()
            
            data = response.json()
            
            videos = []
            for item in data.get('items', []):
                videos.append({
                    'video_id': item['id']['videoId'],
                    'title': item['snippet']['title'],
                    'published': item['snippet']['publishedAt'],
                    'thumbnail': item['snippet']['thumbnails']['medium']['url'],
                    'url': f"https://www.youtube.com/watch?v={item['id']['videoId']}"
                })
            
            logging.info(f"Successfully fetched {len(videos)} videos via YouTube API (API key)")
            return videos
        
    except Exception as e:
        logging.error(f"YouTube API failed: {e}, falling back to RSS")
        # Fallback to RSS
        return get_channel_latest_videos_rss(channel_id, max_results)

def check_channel_video_count_rss(channel_id):
    """Check video count using RSS feed (faster than API)"""
    try:
        import feedparser
        rss_url = f"https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}"
        
        feed = feedparser.parse(rss_url)
        if feed.entries:
            video_count = len(feed.entries)
            logging.info(f"RSS feed check: Found {video_count} recent videos for channel {channel_id}")
            return video_count
        else:
            logging.info(f"RSS feed check: No videos found for channel {channel_id}")
            return 0
        
    except Exception as e:
        logging.error(f"RSS feed check failed for channel {channel_id}: {e}")
        return 0

def get_channel_latest_videos_rss(channel_id, limit=3):
    """Get latest videos using RSS feed"""
    try:
        import feedparser
        rss_url = f"https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}"
        
        feed = feedparser.parse(rss_url)
        videos = []
        
        for entry in feed.entries[:limit]:
            videos.append({
                'video_id': entry.yt_videoid,
                'title': entry.title,
                'published': entry.published,
                'url': entry.link,
                'thumbnail': f"https://i.ytimg.com/vi/{entry.yt_videoid}/mqdefault.jpg"
            })
        
        return videos
        
    except Exception as e:
        logging.error(f"RSS video fetch failed: {e}")
        return []

def format_number_short(number):
    """Format numbers with K, M, B suffixes"""
    if number >= 1_000_000_000:
        return f"{number / 1_000_000_000:.1f}B"
    elif number >= 1_000_000:
        return f"{number / 1_000_000:.1f}M"
    elif number >= 1_000:
        return f"{number / 1_000:.1f}K"
    else:
        return str(number)

def add_automation_log(user_id, log_type, message, flush=False):
    """Add log entry to automation logs with proper formatting"""
    try:
        import asyncio
        from mongo import get_automation_logs, save_automation_logs
        
        logs_data = asyncio.run(get_automation_logs(user_id))
        
        # Create formatted timestamp
        from datetime import datetime
        now = datetime.now()
        formatted_time = now.strftime("%H:%M:%S")
        
        # If flush is True, replace the last log entry if it's a countdown message
        if flush and logs_data['logs'] and '⏳ Cooldown:' in logs_data['logs'][-1].get('message', ''):
            log_entry = {
                'timestamp': time.time() * 1000,
                'type': log_type,
                'message': f"[{formatted_time}] {message}"
            }
            logs_data['logs'][-1] = log_entry
        else:
            log_entry = {
                'timestamp': time.time() * 1000,
                'type': log_type,
                'message': f"[{formatted_time}] {message}"
            }
            logs_data['logs'].append(log_entry)
        
        # Keep only last 1000 logs
        if len(logs_data['logs']) > 1000:
            logs_data['logs'] = logs_data['logs'][-1000:]
        
        asyncio.run(save_automation_logs(user_id, logs_data))
            
    except Exception as e:
        logging.error(f"Error adding automation log: {e}")

def set_automation_service_status(user_id, status):
    """Set automation service status"""
    try:
        import asyncio
        from mongo import get_automation_logs, save_automation_logs
        
        logs_data = asyncio.run(get_automation_logs(user_id))
        logs_data['service_status'] = status
        asyncio.run(save_automation_logs(user_id, logs_data))
            
    except Exception as e:
        logging.error(f"Error setting automation service status: {e}")

def automation_monitor_worker(user_id):
    """Enhanced background worker with real-time countdown, video links, and proper download/upload logic"""
    try:
        set_automation_service_status(user_id, True)
        add_automation_log(user_id, 'success', '🚀 Started Monitoring Service')
        
        while True:
            start_time = time.time()
            try:
                # Check if service should stop
                logs_file = f"db/{user_id}/automation_logs.json"
                if os.path.exists(logs_file):
                    with open(logs_file, 'r') as f:
                        logs_data = json.load(f)
                    if not logs_data.get('service_status', False):
                        break
                
                # Load settings for API key and interval
                import asyncio
                from mongo import get_user_settings, get_user_channels, save_user_channels
                
                settings = asyncio.run(get_user_settings(user_id))
                api_key = settings.get('api_key')
                monitor_interval = settings.get('monitor_interval', 300)
                
                # Load channels
                channels_data = asyncio.run(get_user_channels(user_id))
                channels = channels_data.get('channels', [])
                
                if not channels:
                    add_automation_log(user_id, 'warning', 'No channels configured yet, waiting...')
                    time.sleep(10)
                    continue
                if not channels:
                    add_automation_log(user_id, 'warning', 'No channels to monitor')
                    time.sleep(10)
                    continue
                
                # Build channel names list for logging
                channel_names = [ch.get('name', 'Unknown') for ch in channels]
                channels_str = ', '.join(channel_names)
                
                # Log searching message
                add_automation_log(user_id, 'info', f"🔍 Searching for videos in {channels_str}")
                
                total_new_videos = 0
                new_videos_found = []
                
                # Check each channel for new videos
                for i, channel in enumerate(channels):
                    channel_name = channel.get('name', 'Unknown')
                    channel_id = channel.get('channel_id', '')
                    
                    try:
                        # Use user's API key if available, otherwise use default
                        current_video_count = 0
                        
                        try:
                            from auth_helper import get_channel_details_api_v3
                            channel_details = get_channel_details_api_v3(channel_id, api_key)
                            current_video_count = channel_details.get('video_count', 0)
                            
                        except Exception as api_err:
                            # Fallback to RSS
                            current_video_count = check_channel_video_count_rss(channel_id)
                        
                        last_known_count = channel.get('last_video_count', 0)
                        
                        if current_video_count > last_known_count:
                            new_videos_count = current_video_count - last_known_count
                            total_new_videos += new_videos_count
                            
                            # Update the count
                            channels[i]['last_video_count'] = current_video_count
                            channels[i]['last_checked'] = time.time()
                            
                            # Get latest videos with metadata extraction
                            try:
                                from auth_helper import get_channel_latest_videos_api_v3
                                latest_videos = get_channel_latest_videos_api_v3(channel_id, api_key, new_videos_count)
                                
                                for video in latest_videos:
                                    # Log metadata extraction
                                    add_automation_log(user_id, 'info', f"📄 Extracting video metadata... {video.get('title', 'Unknown')} , {video.get('published_at', 'Unknown date')}")
                                    
                                    try:
                                        # Extract metadata using yt-dlp
                                        from multi_platform_downloader import extract_platform_metadata
                                        metadata = extract_platform_metadata(video.get('url', ''))
                                        add_automation_log(user_id, 'success', f"✅ Successfully Extracted metadata")
                                        add_automation_log(user_id, 'info', f"    📺 {metadata.get('title', 'Unknown')} , {metadata.get('upload_date', 'Unknown date')}")
                                        
                                        # Add to new videos list for processing
                                        new_videos_found.append({
                                            'url': video.get('url', ''),
                                            'title': metadata.get('title', video.get('title', 'Unknown')),
                                            'upload_date': metadata.get('upload_date', video.get('published_at', 'Unknown')),
                                            'metadata': metadata
                                        })
                                        
                                    except Exception as metadata_err:
                                        add_automation_log(user_id, 'error', f"❌ Failed to extract metadata: {str(metadata_err)}")
                                        
                            except Exception as video_err:
                                add_automation_log(user_id, 'warning', f"Could not fetch video details: {str(video_err)}")
                        
                        elif current_video_count < last_known_count:
                            # Video count decreased
                            channels[i]['last_video_count'] = current_video_count
                    
                    except Exception as channel_err:
                        add_automation_log(user_id, 'error', f"❌ Error checking {channel_name}: {str(channel_err)}")
                
                # Log total new videos found
                add_automation_log(user_id, 'info', f"📊 Found {total_new_videos} new videos.")
                
                # Process new videos if found
                if new_videos_found:
                    # Get user's access token for YouTube upload
                    try:
                        # Check if user has valid access token
                        user_dir = f"db/{user_id}"
                        user_data_file = f"{user_dir}/user_data.json"
                        access_token = None
                        
                        # We need to get access token from session, but since this runs in background,
                        # we'll simulate for now and log that we need the token
                        add_automation_log(user_id, 'warning', '⚠️ YouTube upload requires active user session')
                        
                        # Process each video
                        for i, video in enumerate(new_videos_found):
                            video_title = video['title']
                            video_url = video['url']
                            
                            add_automation_log(user_id, 'info', f"⬇️ Downloading: {i+1}/{len(new_videos_found)} - {video_title}")
                            
                            try:
                                # Actual video processing with download and upload
                                add_automation_log(user_id, 'info', f"⬆️ Uploading: {i+1}/{len(new_videos_found)} - {video_title}")
                                
                                # Process video (download and upload)
                                youtube_url = process_video_for_automation(user_id, video_url, video_title, video['metadata'])
                                
                                add_automation_log(user_id, 'success', f"✅ Successfully Downloaded {i+1} video(s)")
                                add_automation_log(user_id, 'success', f"✅ Successfully uploaded {i+1} video(s) - {youtube_url}")
                                    
                            except Exception as process_err:
                                add_automation_log(user_id, 'error', f"❌ Failed to process {video_title}: {str(process_err)}")
                                
                    except Exception as upload_err:
                        add_automation_log(user_id, 'error', f"❌ Upload process error: {str(upload_err)}")
                
                # Save updated channels data
                import asyncio
                from mongo import save_user_channels
                asyncio.run(save_user_channels(user_id, channels_data))
                
                # Cooldown timer with real-time countdown
                add_automation_log(user_id, 'info', f"⏰ STARTING COOLDOWN: {monitor_interval} seconds")
                
                # Real-time countdown - update every second
                remaining = monitor_interval
                while remaining > 0:
                    # Check if service was stopped
                    if os.path.exists(logs_file):
                        with open(logs_file, 'r') as f:
                            logs_data = json.load(f)
                        if not logs_data.get('service_status', False):
                            break
                    
                    # Update countdown every second
                    mins = remaining // 60
                    secs = remaining % 60
                    if mins > 0:
                        countdown_msg = f"⏳ Cooldown: {mins}m {secs}s remaining"
                    else:
                        countdown_msg = f"⏳ Cooldown: {secs}s remaining"
                    
                    add_automation_log(user_id, 'info', countdown_msg, flush=True)
                    
                    time.sleep(1)
                    remaining -= 1
                
            except Exception as e:
                error_msg = f"Monitor cycle error: {str(e)}"
                add_automation_log(user_id, 'error', f"❌ {error_msg}")
                time.sleep(60)  # Wait 1 minute before retrying on error
        
    except Exception as e:
        error_msg = f"Automation monitor crashed: {str(e)}"
        add_automation_log(user_id, 'error', f"💥 {error_msg}")
    finally:
        set_automation_service_status(user_id, False)
        add_automation_log(user_id, 'info', '🛑 Monitoring service stopped')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)

@app.route('/test_simple')
def test_simple():
    """Simple test of core functionality"""
    from simple_test import run_simple_test

    try:
        results = run_simple_test()

        html_result = "<h2>⚡ Simple Core Functionality Test</h2>"

        success_count = len([r for r in results if r['status'] == 'success'])
        total_count = len(results)

        if success_count == total_count:
            html_result += "<div class='alert alert-success'><strong>✅ All tests passed!</strong></div>"
        else:
            html_result += f"<div class='alert alert-warning'><strong>⚠️ {success_count}/{total_count} tests passed</strong></div>"

        for result in results:
            if result['status'] == 'success':
                html_result += f"<div class='card border-success mb-3'>"
                html_result += f"<div class='card-header bg-success bg-opacity-10'>"
                html_result += f"<h6>✅ Test {result['test_number']}: {result['platform']}</h6>"
                html_result += f"</div><div class='card-body'>"
                html_result += f"<p><strong>Title:</strong> {result['title']}</p>"
                html_result += f"<p><strong>Creator:</strong> {result['uploader']}</p>"
                html_result += f"<p><strong>Duration:</strong> {result['duration']}</p>"
            else:
                html_result += f"<div class='card border-danger mb-3'>"
                html_result += f"<div class='card-header bg-danger bg-opacity-10'>"
                html_result += f"<h6>❌ Test {result['test_number']}: {result['platform']}</h6>"
                html_result += f"</div><div class='card-body'>"
                html_result += f"<p><strong>Error:</strong> {result.get('error', 'Unknown error')}</p>"

            html_result += f"<small class='text-muted'>URL: {result['url']}</small>"
            html_result += f"</div></div>"

        return html_result

    except Exception as e:
        return f"<h2>Test Error</h2><p style='color: red;'>Failed to run simple test: {str(e)}</p>"