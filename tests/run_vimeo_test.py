
#!/usr/bin/env python3
"""
Simple script to test Vimeo functionality
"""

def main():
    print("Testing Vimeo integration...")
    
    try:
        from test_vimeo import test_vimeo_with_cookies, test_vimeo_integration
        
        print("Running Vimeo tests...")
        test_vimeo_with_cookies()
        test_vimeo_integration()
        
        print("\n" + "="*50)
        print("✓ Vimeo testing completed successfully!")
        print("You can now:")
        print("1. Visit /test_vimeo in your web app")
        print("2. Try extracting metadata from Vimeo URLs")
        print("3. Download videos from Vimeo (if authenticated)")
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("Make sure all dependencies are installed")
    except Exception as e:
        print(f"❌ Test error: {e}")

if __name__ == "__main__":
    main()
