#!/usr/bin/env python3
"""
Test script for PostgreSQL database tools.

This script tests the database tools functionality including:
- Database connection
- Table listing
- Schema retrieval
- Query validation
- Query execution

Run with: python test_database.py
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add the current directory to Python path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from tools.database import (
    list_database_tables,
    get_database_schema,
    query_database,
    check_database_query,
    get_database_manager
)

def test_database_connection():
    """Test database connection."""
    print("🔌 Testing database connection...")
    
    try:
        db_manager = get_database_manager()
        if db_manager is None:
            print("❌ Database connection failed: Missing environment variables")
            print("   Please set DB_NAME, DB_USER, DB_PASSWORD in your .env file")
            return False
        
        db = db_manager.get_db()
        print("✅ Database connection successful")
        return True
    
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False

def test_list_tables():
    """Test listing database tables."""
    print("\n📋 Testing table listing...")
    
    try:
        result = list_database_tables.invoke({})
        print(f"✅ Tables listed: {result}")
        return True
    
    except Exception as e:
        print(f"❌ Table listing failed: {e}")
        return False

def test_schema_retrieval():
    """Test schema retrieval for a common table."""
    print("\n🏗️  Testing schema retrieval...")
    
    # First get available tables
    tables_result = list_database_tables.invoke({})
    
    if "Available tables:" in tables_result:
        # Extract first table name for testing
        tables_list = tables_result.replace("Available tables: ", "").split(", ")
        if tables_list and tables_list[0]:
            test_table = tables_list[0].strip()
            print(f"   Testing with table: {test_table}")
            
            try:
                result = get_database_schema.invoke({"table_names": test_table})
                print(f"✅ Schema retrieved for {test_table}")
                print(f"   Schema info: {result[:200]}...")  # Show first 200 chars
                return True
            
            except Exception as e:
                print(f"❌ Schema retrieval failed: {e}")
                return False
    
    print("⚠️  No tables available for schema testing")
    return True

def test_query_validation():
    """Test query validation."""
    print("\n🔍 Testing query validation...")
    
    test_queries = [
        "SELECT 1",  # Simple valid query
        "SELECT * FROM nonexistent_table",  # Invalid table
        "DROP TABLE test",  # Dangerous query
        "INSERT INTO test VALUES (1)",  # Non-SELECT query
    ]
    
    for query in test_queries:
        print(f"   Testing query: {query}")
        try:
            result = check_database_query.invoke({"query": query})
            print(f"   Result: {result[:100]}...")
        except Exception as e:
            print(f"   Error: {e}")
    
    print("✅ Query validation tests completed")
    return True

def test_query_execution():
    """Test query execution."""
    print("\n🚀 Testing query execution...")
    
    # Test simple query
    simple_query = "SELECT 1 as test_number, 'Hello Database' as test_message"
    
    try:
        result = query_database.invoke({"query": simple_query})
        print(f"✅ Simple query executed successfully")
        print(f"   Result: {result[:200]}...")
        return True
    
    except Exception as e:
        print(f"❌ Query execution failed: {e}")
        return False

def test_security_features():
    """Test security features."""
    print("\n🔒 Testing security features...")
    
    dangerous_queries = [
        "DROP TABLE users",
        "DELETE FROM customers",
        "UPDATE products SET price = 0",
        "INSERT INTO logs VALUES ('test')",
        "CREATE TABLE malicious (id INT)",
    ]
    
    all_blocked = True
    for query in dangerous_queries:
        try:
            result = query_database.invoke({"query": query})
            if "Only SELECT queries are allowed" in result:
                print(f"✅ Dangerous query blocked: {query}")
            else:
                print(f"❌ Security bypass detected: {query}")
                all_blocked = False
        except Exception as e:
            print(f"✅ Dangerous query blocked with exception: {query}")
    
    if all_blocked:
        print("✅ All security tests passed")
    else:
        print("❌ Some security tests failed")
    
    return all_blocked

def main():
    """Run all database tests."""
    print("🧪 PostgreSQL Database Tools Test Suite")
    print("=" * 50)
    
    # Check environment variables
    required_vars = ["DB_NAME", "DB_USER", "DB_PASSWORD"]
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        print(f"❌ Missing required environment variables: {', '.join(missing_vars)}")
        print("   Please create a .env file with database configuration")
        print("   Example:")
        print("   DB_HOST=localhost")
        print("   DB_PORT=5432")
        print("   DB_NAME=your_database")
        print("   DB_USER=your_user")
        print("   DB_PASSWORD=your_password")
        sys.exit(1)
    
    # Run tests
    tests = [
        ("Database Connection", test_database_connection),
        ("List Tables", test_list_tables),
        ("Schema Retrieval", test_schema_retrieval),
        ("Query Validation", test_query_validation),
        ("Query Execution", test_query_execution),
        ("Security Features", test_security_features),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n📊 Running: {test_name}")
        try:
            if test_func():
                passed += 1
        except Exception as e:
            print(f"❌ Test '{test_name}' failed with exception: {e}")
    
    # Summary
    print("\n" + "=" * 50)
    print(f"🏁 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Database tools are working correctly.")
        sys.exit(0)
    else:
        print("⚠️  Some tests failed. Please check your database configuration.")
        sys.exit(1)

if __name__ == "__main__":
    main()