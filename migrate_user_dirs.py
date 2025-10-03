
import os
import json
import shutil
from auth_helper import get_user_info

def migrate_user_directories():
    """Migrate existing user directories from user_id to email-based naming"""
    db_dir = "db"
    
    if not os.path.exists(db_dir):
        print("No db directory found")
        return
    
    for item in os.listdir(db_dir):
        item_path = os.path.join(db_dir, item)
        
        # Skip non-directories and already converted directories
        if not os.path.isdir(item_path) or '_' in item:
            continue
        
        # Check if it's a numeric user ID (Google user IDs are numeric)
        if not item.isdigit():
            continue
        
        print(f"Processing user directory: {item}")
        
        # Try to find email from existing tokens or user data
        tokens_file = os.path.join(item_path, "tokens.json")
        user_data_file = os.path.join(item_path, "user_data.json")
        
        user_email = None
        
        # Try to get email from tokens
        if os.path.exists(tokens_file):
            try:
                with open(tokens_file, 'r') as f:
                    tokens_data = json.load(f)
                    
                access_token = tokens_data.get('access_token')
                if access_token:
                    try:
                        user_info = get_user_info(access_token)
                        user_email = user_info.get('email')
                        print(f"Found email from tokens: {user_email}")
                    except Exception as e:
                        print(f"Could not get user info from token: {e}")
            except Exception as e:
                print(f"Error reading tokens file: {e}")
        
        # Try to get email from user data file
        if not user_email and os.path.exists(user_data_file):
            try:
                with open(user_data_file, 'r') as f:
                    user_data = json.load(f)
                    user_email = user_data.get('email')
                    print(f"Found email from user data: {user_email}")
            except Exception as e:
                print(f"Error reading user data file: {e}")
        
        if not user_email:
            print(f"Could not find email for user {item}, skipping migration")
            continue
        
        # Convert email to directory name
        new_dir_name = user_email.replace('@', '_').replace('.', '_')
        new_path = os.path.join(db_dir, new_dir_name)
        
        # Check if new directory already exists
        if os.path.exists(new_path):
            print(f"Directory {new_dir_name} already exists, skipping")
            continue
        
        try:
            # Rename directory
            shutil.move(item_path, new_path)
            print(f"Successfully migrated {item} -> {new_dir_name}")
            
            # Update any internal references if needed
            update_internal_references(new_path, item, new_dir_name)
            
        except Exception as e:
            print(f"Error migrating {item}: {e}")

def update_internal_references(dir_path, old_id, new_id):
    """Update any internal file references from old user_id to new email-based id"""
    try:
        # Update automation logs if they contain old user ID references
        logs_file = os.path.join(dir_path, "automation_logs.json")
        if os.path.exists(logs_file):
            with open(logs_file, 'r') as f:
                logs_data = json.load(f)
            
            # Update any log messages that might contain the old ID
            updated = False
            if 'logs' in logs_data:
                for log in logs_data['logs']:
                    if old_id in log.get('message', ''):
                        log['message'] = log['message'].replace(old_id, new_id)
                        updated = True
            
            if updated:
                with open(logs_file, 'w') as f:
                    json.dump(logs_data, f, indent=2)
                print(f"Updated log references in {logs_file}")
        
    except Exception as e:
        print(f"Error updating internal references: {e}")

if __name__ == "__main__":
    print("Starting user directory migration...")
    migrate_user_directories()
    print("Migration completed!")
