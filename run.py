
#!/usr/bin/env python3
import os
import sys
import subprocess

def install_requirements():
    """Install requirements from requirements.txt"""
    print("📦 Installing dependencies...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("✅ Dependencies installed successfully!")
    except subprocess.CalledProcessError as e:
        print(f"❌ Error installing dependencies: {e}")
        sys.exit(1)

def main():
    """Main entry point - install deps and run app"""
    # Install requirements if not already installed
    install_requirements()
    
    # Import and run the app
    from app import app
    
    # Get port from environment or use default
    port = int(os.environ.get('PORT', 5000))
    
    print(f"🚀 Starting UpDownVid on http://0.0.0.0:{port}")
    print("Press CTRL+C to quit")
    
    # Run the Flask app
    app.run(host='0.0.0.0', port=port, debug=os.environ.get('DEBUG', 'False').lower() == 'true')

if __name__ == '__main__':
    main()
