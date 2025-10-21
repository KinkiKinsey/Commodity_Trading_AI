"""
Macro Risk Analysis Module

Retrieves macro economic analysis from Redis database.
"""

import json
import redis
import os


def get_macro_risk_analysis() -> str:
    """
    Get macro risk analysis from Redis database.
    
    Returns:
        Comprehensive macro analysis string containing:
        - US GDP Growth analysis
        - Unemployment Rate trends
        - Inflation impact on commodities
        - Business cycle phase identification
        - Risk scenarios (Path 1, 2, 3)
        - Global commodity market implications
        
    Returns None if data is unavailable or error occurs.
    
    Example:
        >>> analysis = get_macro_risk_analysis()
        >>> if analysis:
        >>>     print(analysis)
    """
    try:
        print("🔍 Retrieving Macro Analysis from Redis...")
        
        # Connect to Redis with environment variable support
        redis_config = {
            "host": os.getenv("RINGSHELL_REDIS_HOST"),
            "port": int(os.getenv("RINGSHELL_REDIS_PORT")),
            "username": os.getenv("RINGSHELL_REDIS_USERNAME"),
            "password": os.getenv("RINGSHELL_REDIS_PASSWORD"),
            "decode_responses": True
        }
        
        r = redis.Redis(**redis_config)
        
        # Get the LLM analysis
        analysis_key = "Macro_Event:Blackswan:LLM_Analysis"
        analysis_data = r.get(analysis_key)
        
        if not analysis_data:
            print("❌ No macro analysis found in Redis")
            return None
        
        # Parse the JSON data
        data = json.loads(analysis_data)
        
        print("✅ Macro Analysis Retrieved!")
        return data['analysis']
        
    except Exception as e:
        print(f"❌ Error retrieving macro analysis: {e}")
        return None

