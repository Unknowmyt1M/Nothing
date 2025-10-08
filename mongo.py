
import os
import motor.motor_asyncio
from dotenv import load_dotenv
import logging
from pymongo.errors import CollectionInvalid

# Load environment variables
load_dotenv()

# MongoDB configuration
MONGO_URL = os.environ.get('MONGO_URL')
DB_NAME = os.environ.get('DB_NAME', 'updownvid')

if not MONGO_URL:
    raise Exception("MONGO_URL not found in environment variables")

# Create async MongoDB client
client = motor.motor_asyncio.AsyncIOMotorClient(MONGO_URL)
db = client[DB_NAME]

# Collection names
USERS_COLLECTION = 'users'
TOKENS_COLLECTION = 'tokens'
HISTORY_COLLECTION = 'history'
SETTINGS_COLLECTION = 'settings'
CHANNELS_COLLECTION = 'channels'
LOGS_COLLECTION = 'automation_logs'

async def database_init():
    """Initialize database and create collections if they don't exist"""
    try:
        # Test connection
        await client.admin.command('ping')
        logging.info("✅ MongoDB connection successful")
        
        # Get existing collections
        existing_collections = await db.list_collection_names()
        
        # Create collections if they don't exist
        collections_to_create = [
            USERS_COLLECTION,
            TOKENS_COLLECTION,
            HISTORY_COLLECTION,
            SETTINGS_COLLECTION,
            CHANNELS_COLLECTION,
            LOGS_COLLECTION
        ]
        
        for collection_name in collections_to_create:
            if collection_name not in existing_collections:
                await db.create_collection(collection_name)
                logging.info(f"✅ New Collection created - {collection_name}")
        
        # Create indexes for better query performance
        await db[TOKENS_COLLECTION].create_index('user_id', unique=True)
        await db[SETTINGS_COLLECTION].create_index('user_id', unique=True)
        await db[CHANNELS_COLLECTION].create_index('user_id')
        await db[HISTORY_COLLECTION].create_index('user_id')
        await db[LOGS_COLLECTION].create_index('user_id')
        
        logging.info("✅ Database initialization complete")
        
    except Exception as e:
        logging.error(f"❌ Database initialization failed: {e}")
        raise

# Helper functions for common operations
async def get_user_tokens(user_id):
    """Get user tokens from database"""
    result = await db[TOKENS_COLLECTION].find_one({'user_id': user_id})
    return result if result else None

async def store_user_tokens(user_id, access_token, refresh_token):
    """Store user tokens in database"""
    data = {
        'user_id': user_id,
        'access_token': access_token,
        'refresh_token': refresh_token
    }
    result = await db[TOKENS_COLLECTION].update_one(
        {'user_id': user_id},
        {'$set': data},
        upsert=True
    )
    logging.info(f"✅ New Data stored - User tokens for {user_id}")
    return result

async def get_user_settings(user_id):
    """Get user settings from database"""
    result = await db[SETTINGS_COLLECTION].find_one({'user_id': user_id})
    if result:
        return result
    return {
        'monitor_interval': 300,
        'quality': '1080p',
        'metadata_mode': 'original',
        'custom_metadata': {
            'title': '',
            'description': '',
            'tags': []
        }
    }

async def save_user_settings(user_id, settings):
    """Save user settings to database"""
    settings['user_id'] = user_id
    result = await db[SETTINGS_COLLECTION].update_one(
        {'user_id': user_id},
        {'$set': settings},
        upsert=True
    )
    logging.info(f"✅ New Data stored - User settings for {user_id}")
    return result

async def get_user_channels(user_id):
    """Get user's monitored channels"""
    result = await db[CHANNELS_COLLECTION].find_one({'user_id': user_id})
    if result:
        return result
    return {'channels': []}

async def save_user_channels(user_id, channels_data):
    """Save user's monitored channels"""
    channels_data['user_id'] = user_id
    result = await db[CHANNELS_COLLECTION].update_one(
        {'user_id': user_id},
        {'$set': channels_data},
        upsert=True
    )
    logging.info(f"✅ New Data stored - User channels for {user_id}")
    return result

async def get_automation_logs(user_id):
    """Get automation logs for user"""
    result = await db[LOGS_COLLECTION].find_one({'user_id': user_id})
    if result:
        return result
    return {'logs': [], 'service_status': False}

async def save_automation_logs(user_id, logs_data):
    """Save automation logs for user"""
    logs_data['user_id'] = user_id
    result = await db[LOGS_COLLECTION].update_one(
        {'user_id': user_id},
        {'$set': logs_data},
        upsert=True
    )
    return result

async def add_to_history(user_id, upload_data):
    """Add upload to user history"""
    result = await db[HISTORY_COLLECTION].update_one(
        {'user_id': user_id},
        {'$push': {'uploads': {'$each': [upload_data], '$slice': -50}}},
        upsert=True
    )
    logging.info(f"✅ New Data stored - Upload history for {user_id}")
    return result

async def get_user_history(user_id):
    """Get user upload history"""
    result = await db[HISTORY_COLLECTION].find_one({'user_id': user_id})
    if result and 'uploads' in result:
        return result['uploads']
    return []
