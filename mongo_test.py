
import os
import asyncio
from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime

# Load environment variables
load_dotenv()

async def test_mongodb_connection():
    """Test MongoDB connection and basic operations"""
    
    print("=" * 60)
    print("🔍 MONGODB CONNECTION TEST")
    print("=" * 60)
    
    # Get MongoDB credentials
    MONGO_URL = os.environ.get('MONGO_URL')
    DB_NAME = os.environ.get('DB_NAME', 'updownvid')
    
    if not MONGO_URL:
        print("❌ ERROR: MONGO_URL not found in .env file")
        print("💡 Please add MONGO_URL to your .env file")
        return False
    
    print(f"\n📋 Configuration:")
    print(f"   Database: {DB_NAME}")
    print(f"   Connection URL: {MONGO_URL[:30]}..." if len(MONGO_URL) > 30 else MONGO_URL)
    
    try:
        # Step 1: Connect to MongoDB
        print("\n🔌 Step 1: Connecting to MongoDB...")
        client = AsyncIOMotorClient(MONGO_URL)
        db = client[DB_NAME]
        
        # Test connection with ping
        await client.admin.command('ping')
        print("   ✅ Successfully connected to MongoDB")
        
        # Step 2: Create a test collection
        print("\n📦 Step 2: Creating test collection...")
        test_collection = db['test_collection']
        
        # Check if collection exists
        collections = await db.list_collection_names()
        if 'test_collection' in collections:
            print("   ℹ️  Test collection already exists")
        else:
            await db.create_collection('test_collection')
            print("   ✅ Test collection created successfully")
        
        # Step 3: Insert test data
        print("\n💾 Step 3: Inserting test data...")
        test_data = {
            'test_id': 'test_001',
            'message': 'Hello from MongoDB test!',
            'timestamp': datetime.now().isoformat(),
            'status': 'active'
        }
        
        result = await test_collection.insert_one(test_data)
        print(f"   ✅ Test data inserted with ID: {result.inserted_id}")
        
        # Step 4: Read the data back
        print("\n📖 Step 4: Reading test data...")
        retrieved_data = await test_collection.find_one({'test_id': 'test_001'})
        
        if retrieved_data:
            print("   ✅ Successfully retrieved test data:")
            print(f"      - Message: {retrieved_data.get('message')}")
            print(f"      - Timestamp: {retrieved_data.get('timestamp')}")
            print(f"      - Status: {retrieved_data.get('status')}")
        
        # Step 5: Update the data
        print("\n🔄 Step 5: Updating test data...")
        update_result = await test_collection.update_one(
            {'test_id': 'test_001'},
            {'$set': {'status': 'updated', 'update_time': datetime.now().isoformat()}}
        )
        print(f"   ✅ Updated {update_result.modified_count} document(s)")
        
        # Step 6: Count documents
        print("\n🔢 Step 6: Counting documents...")
        count = await test_collection.count_documents({})
        print(f"   ✅ Total documents in test collection: {count}")
        
        # Step 7: Clean up test data
        print("\n🧹 Step 7: Cleaning up test data...")
        delete_result = await test_collection.delete_many({'test_id': 'test_001'})
        print(f"   ✅ Deleted {delete_result.deleted_count} test document(s)")
        
        print("\n" + "=" * 60)
        print("🎉 ALL TESTS PASSED SUCCESSFULLY!")
        print("=" * 60)
        print("\n✅ Your MongoDB connection is working properly")
        print("✅ Database operations are functioning correctly")
        print("\n💡 You can now use MongoDB in your application")
        
        # Close connection
        client.close()
        return True
        
    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        print("\n💡 Troubleshooting tips:")
        print("   1. Check if MONGO_URL is correct in .env file")
        print("   2. Ensure MongoDB server is running and accessible")
        print("   3. Verify network connectivity to MongoDB")
        print("   4. Check if database user has proper permissions")
        return False

if __name__ == "__main__":
    print("\n🚀 Starting MongoDB Connection Test...\n")
    success = asyncio.run(test_mongodb_connection())
    
    if success:
        print("\n✅ Test completed successfully!")
        exit(0)
    else:
        print("\n❌ Test failed. Please check the errors above.")
        exit(1)
