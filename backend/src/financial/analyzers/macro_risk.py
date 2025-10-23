"""
Macro Risk Analysis Module

Retrieves macro economic analysis from Redis database.
"""

import json
import redis
import ssl as ssl_module
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
        host = os.getenv("RINGSHELL_REDIS_HOST", "localhost")
        port = int(os.getenv("RINGSHELL_REDIS_PORT", 6379))
        username = os.getenv("RINGSHELL_REDIS_USERNAME", "")
        password = os.getenv("RINGSHELL_REDIS_PASSWORD", "")
        
        # Use connection URL format for Redis Cloud
        if port != 6379 or 'redis-cloud' in host or 'redislabs' in host or 'redns' in host:
            # Try SSL first, fallback to non-SSL if it fails
            try:
                # Redis Cloud URL format with SSL
                url = f"rediss://{username}:{password}@{host}:{port}"
                r = redis.from_url(
                    url, 
                    decode_responses=True, 
                    ssl_cert_reqs=None,
                    socket_connect_timeout=5,
                    socket_keepalive=True
                )
                # Test connection
                r.ping()
            except Exception:
                # Fallback to non-SSL connection
                url = f"redis://{username}:{password}@{host}:{port}"
                r = redis.from_url(url, decode_responses=True, socket_connect_timeout=5)
        else:
            # Local Redis connection
            redis_config = {
                "host": host,
                "port": port,
                "username": username if username else None,
                "password": password if password else None,
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

