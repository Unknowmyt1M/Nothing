import os
import sys
import asyncio
import logging

# Import app at module level for gunicorn compatibility
from app import app

async def init_database():
    """Initialize MongoDB connection"""
    try:
        from mongo import database_init
        print("🔌 Connecting to MongoDB...")
        await database_init()
        print("✅ MongoDB initialized successfully")
    except Exception as e:
        logging.error(f"❌ Failed to initialize database: {e}")
        print(f"❌ MongoDB Error: {e}")
        print("💡 Please run 'python mongo_test.py' to test your MongoDB connection")
        sys.exit(1)

def main():
    """Main entry point for the application"""
    # Initialize database
    asyncio.run(init_database())
    
    # Get port from environment or use default
    port = int(os.environ.get('PORT', 5000))
    
    try:
        print(f"Starting YouTube Auto Uploader on http://0.0.0.0:{port}")
        print("Press CTRL+C to quit")
        
        # Start the Flask development server
        app.run(host='0.0.0.0', port=port, debug=True)
        
    except ImportError as e:
        print(f"❌ Import Error: {e}")
        print("💡 Make sure to install dependencies with: pip install -r requirements.txt")
        sys.exit(1)
    except OSError as e:
        if "Address already in use" in str(e):
            print(f"❌ Port {port} is already in use!")
            print("💡 Try using a different port: PORT=5001 python main.py")
        else:
            print(f"❌ OS Error: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n👋 Shutting down gracefully...")
        sys.exit(0)
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
