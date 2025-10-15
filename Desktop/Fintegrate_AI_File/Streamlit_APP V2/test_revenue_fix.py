#!/usr/bin/env python3
"""
Test script to verify Revenue Segmentation database fixes.
"""

import sys
import os
from pathlib import Path

# Add current directory to Python path
current_dir = Path(__file__).parent.absolute()
sys.path.append(str(current_dir))

from Revenue_Segmentation_DB_Agent import RevenueSegmentationDatabaseStorage
from Revenue_Segmentation_Read_Agent import RevenueSegmentationAnalystAgent

def test_database_fixes():
    """Test the database fixes."""
    print("🧪 Testing Revenue Segmentation Database Fixes")
    print("=" * 50)
    
    # Test 1: Test DB Agent
    print("\n1️⃣ Testing Revenue Segmentation DB Agent...")
    try:
        db_agent = RevenueSegmentationDatabaseStorage(
            db_type="redis",
            host="redis-16376.crce197.us-east-2-1.ec2.redns.redis-cloud.com",
            port=16376,
            username="default",
            password="rl8242B4UItBhFzgHW5APEqZnkYoaEZv"
        )
        
        # Test database connection
        connection_ok = db_agent.test_database_connection("COIN")
        if connection_ok:
            print("✅ DB Agent connection test passed")
        else:
            print("❌ DB Agent connection test failed")
        
        # Test data retrieval
        existing_data = db_agent.get_revenue_segmentation_data("COIN", "Revenue_Segmentation_INFOS")
        if existing_data:
            print(f"✅ Found existing data for COIN")
            print(f"   - Revenue segments: {len(existing_data.get('revenue_segmentation', {}).get('business_segments', []))}")
            print(f"   - Last update: {existing_data.get('metadata', {}).get('last_update', 'Unknown')}")
        else:
            print("📭 No existing data found for COIN")
        
        db_agent.close()
        
    except Exception as e:
        print(f"❌ DB Agent test failed: {e}")
    
    # Test 2: Test Read Agent
    print("\n2️⃣ Testing Revenue Segmentation Read Agent...")
    try:
        read_agent = RevenueSegmentationAnalystAgent(
            redis_host="redis-16376.crce197.us-east-2-1.ec2.redns.redis-cloud.com",
            redis_port=16376,
            redis_username="default",
            redis_password="rl8242B4UItBhFzgHW5APEqZnkYoaEZv",
            collection_name="Revenue_Segmentation_INFOS"
        )
        
        # Test data retrieval
        existing_data = read_agent.get_revenue_segmentation_data("COIN")
        if existing_data:
            print(f"✅ Read Agent found data for COIN")
            print(f"   - Revenue segments: {len(existing_data.get('revenue_segmentation', {}).get('business_segments', []))}")
        else:
            print("📭 Read Agent found no data for COIN")
        
        # Test available tickers
        available_tickers = read_agent.list_available_tickers()
        print(f"📋 Available tickers: {available_tickers}")
        
    except Exception as e:
        print(f"❌ Read Agent test failed: {e}")
    
    print("\n" + "=" * 50)
    print("🏁 Test completed!")

if __name__ == "__main__":
    test_database_fixes()
