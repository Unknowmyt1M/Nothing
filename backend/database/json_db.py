import os
import json
import logging
import threading

# Global thread lock for file operations to prevent race conditions
_db_lock = threading.Lock()

# Define local database directory at the project root level (outside backend folder)
# This keeps database files in one common directory: Nothing-main/db/
DB_DIR = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'db'))

def database_init():
    """Initialize database and create core db folder if not exists"""
    with _db_lock:
        try:
            if not os.path.exists(DB_DIR):
                os.makedirs(DB_DIR, exist_ok=True)
                logging.info(f"✅ Local JSON Database initialized at {DB_DIR}")
            else:
                logging.info(f"✅ Local JSON Database directory verified at {DB_DIR}")
        except Exception as e:
            logging.error(f"❌ Failed to initialize JSON database directory: {e}")
            raise

def _get_user_dir(user_id):
    """Get absolute path to user data folder and create it if missing"""
    # Clean user_id to prevent directory traversal
    clean_id = "".join([c for c in user_id if c.isalnum() or c in ['_', '-']]).strip()
    if not clean_id:
        clean_id = "default_user"
    
    user_path = os.path.join(DB_DIR, clean_id)
    os.makedirs(user_path, exist_ok=True)
    return user_path

def _read_json_file(file_path, default_data):
    """Safely read data from a JSON file with thread lock"""
    with _db_lock:
        if not os.path.exists(file_path):
            return default_data
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logging.error(f"Error reading JSON file {file_path}: {e}")
            return default_data

def _write_json_file(file_path, data):
    """Safely write data to a JSON file with thread lock"""
    with _db_lock:
        try:
            temp_path = file_path + '.tmp'
            with open(temp_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=4, ensure_ascii=False)
            if os.path.exists(file_path):
                os.remove(file_path)
            os.rename(temp_path, file_path)
            return True
        except Exception as e:
            logging.error(f"Error writing JSON file {file_path}: {e}")
            if os.path.exists(file_path + '.tmp'):
                try:
                    os.remove(file_path + '.tmp')
                except:
                    pass
            return False

# Token Helpers
def get_user_tokens(user_id):
    """Get user tokens from local database"""
    user_dir = _get_user_dir(user_id)
    file_path = os.path.join(user_dir, 'tokens.json')
    return _read_json_file(file_path, None)

def store_user_tokens(user_id, access_token, refresh_token):
    """Store user tokens in local database"""
    user_dir = _get_user_dir(user_id)
    file_path = os.path.join(user_dir, 'tokens.json')
    data = {
        'user_id': user_id,
        'access_token': access_token,
        'refresh_token': refresh_token
    }
    logging.info(f"✅ User tokens stored locally for {user_id}")
    return _write_json_file(file_path, data)

# Settings Helpers
def get_user_settings(user_id):
    """Get user settings from local database"""
    user_dir = _get_user_dir(user_id)
    file_path = os.path.join(user_dir, 'settings.json')
    default_settings = {
        'monitor_interval': 300,
        'quality': '1080p',
        'metadata_mode': 'original',
        'custom_metadata': {
            'title': '',
            'description': '',
            'tags': []
        }
    }
    return _read_json_file(file_path, default_settings)

def save_user_settings(user_id, settings):
    """Save user settings to local database"""
    user_dir = _get_user_dir(user_id)
    file_path = os.path.join(user_dir, 'settings.json')
    settings['user_id'] = user_id
    logging.info(f"✅ User settings stored locally for {user_id}")
    return _write_json_file(file_path, settings)

# Channels Helpers
def get_user_channels(user_id):
    """Get user's monitored channels"""
    user_dir = _get_user_dir(user_id)
    file_path = os.path.join(user_dir, 'channels.json')
    return _read_json_file(file_path, {'channels': []})

def save_user_channels(user_id, channels_data):
    """Save user's monitored channels"""
    user_dir = _get_user_dir(user_id)
    file_path = os.path.join(user_dir, 'channels.json')
    channels_data['user_id'] = user_id
    logging.info(f"✅ Monitored channels stored locally for {user_id}")
    return _write_json_file(file_path, channels_data)

# OAuth Tokens Helpers (for full token.json data)
def get_oauth_tokens(user_id):
    """Get OAuth tokens (token.json data) from local database"""
    user_dir = _get_user_dir(user_id)
    file_path = os.path.join(user_dir, 'oauth_tokens.json')
    return _read_json_file(file_path, None)

def save_oauth_tokens(user_id, token_data):
    """Save OAuth tokens (token.json data) to local database"""
    user_dir = _get_user_dir(user_id)
    file_path = os.path.join(user_dir, 'oauth_tokens.json')
    data = {
        'user_id': user_id,
        'tokens': token_data
    }
    logging.info(f"✅ OAuth credentials stored locally for {user_id}")
    return _write_json_file(file_path, data)

def delete_oauth_tokens(user_id):
    """Delete OAuth tokens from local database"""
    user_dir = _get_user_dir(user_id)
    file_path = os.path.join(user_dir, 'oauth_tokens.json')
    with _db_lock:
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
                logging.info(f"🗑️ Deleted OAuth tokens for {user_id}")
                return True
            except Exception as e:
                logging.error(f"Error deleting OAuth tokens file: {e}")
                return False
        return True

# Automation Logs Helpers
def get_automation_logs(user_id):
    """Get automation logs for user"""
    user_dir = _get_user_dir(user_id)
    file_path = os.path.join(user_dir, 'automation_logs.json')
    return _read_json_file(file_path, {'logs': [], 'service_status': False})

def save_automation_logs(user_id, logs_data):
    """Save automation logs for user"""
    user_dir = _get_user_dir(user_id)
    file_path = os.path.join(user_dir, 'automation_logs.json')
    logs_data['user_id'] = user_id
    return _write_json_file(file_path, logs_data)

# History Helpers
def get_user_history(user_id):
    """Get user upload history"""
    user_dir = _get_user_dir(user_id)
    file_path = os.path.join(user_dir, 'history.json')
    return _read_json_file(file_path, [])

def add_to_history(user_id, upload_data):
    """Add upload record to user history (limits to last 50 entries)"""
    user_dir = _get_user_dir(user_id)
    file_path = os.path.join(user_dir, 'history.json')
    history = get_user_history(user_id)
    if not isinstance(history, list):
        history = []
    history.append(upload_data)
    if len(history) > 50:
        history = history[-50:]
    logging.info(f"✅ History entry added locally for {user_id}")
    return _write_json_file(file_path, history)
