"""Test script for the new FastAPI backend"""
import sys
import os

# Add the backend directory to path
sys.path.insert(0, os.path.dirname(__file__))

def test_imports():
    """Test that all modules can be imported"""
    try:
        from backend.main import create_app
        from backend.config import DATABASE_URL
        from backend.db.database import init_db, close_db, get_db_session
        print("✅ All imports successful")
        return True
    except Exception as e:
        print(f"❌ Import error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_app_creation():
    """Test FastAPI app creation"""
    try:
        from backend.main import create_app
        app = create_app()
        print(f"✅ FastAPI app created successfully")
        print(f"   Title: {app.title}")
        print(f"   Version: {app.version}")
        return True
    except Exception as e:
        print(f"❌ App creation error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_database_init():
    """Test database initialization"""
    try:
        from backend.db.database import init_db, close_db
        init_db()
        print("✅ Database initialized successfully")
        
        # Check if tables were created
        from sqlalchemy import create_engine, inspect
        engine = create_engine("sqlite+aiosync:///./nothing_main.db")
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        print(f"   Created tables: {tables}")
        
        close_db()
        return True
    except Exception as e:
        print(f"❌ Database init error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("=== UpDownVid Backend Test ===\n")
    
    results = []
    results.append(("Imports", test_imports()))
    results.append(("App Creation", test_app_creation()))
    results.append(("Database Init", test_database_init()))
    
    print("\n" + "=" * 40)
    print("Summary:")
    for name, passed in results:
        status = "PASS" if passed else "FAIL"
        print(f"  {status}: {name}")
    
    all_passed = all(passed for _, passed in results)
    print(f"\nOverall: {'✅ ALL TESTS PASSED' if all_passed else '❌ SOME TESTS FAILED'}")
    sys.exit(0 if all_passed else 1)