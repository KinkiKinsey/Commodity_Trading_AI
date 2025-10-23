"""
Get Factor Metrics - Clean Pipeline
====================================
This script provides a simple interface to get impact metrics and factor dates.

Input: ticker, language
Output: impact_metrics_df, factor_time_df
"""

import sys
from pathlib import Path
import asyncio
from datetime import datetime, timedelta
from io import StringIO
import pandas as pd

# Add workspace root to path
workspace_root = Path(__file__).parent.parent
if str(workspace_root) not in sys.path:
    sys.path.insert(0, str(workspace_root))

# Import all needed modules
from .LLM_Trend_Summary import get_llm_trend_summary
from DataBase_Connection_Source.RedisDatabaseStorage import RedisDatabaseStorage
from .Oil_Impact_Metrics import get_oil_impact_from_existing_trends
from .Oil_Incremental_Update import incremental_update_oil_metrics


async def get_factor_metrics(ticker: str = "CLZ25.NYM", language: str = "English", force_refresh: bool = False):
    """
    Get impact metrics and factor dates for a given ticker.
    
    Args:
        ticker (str): Oil futures ticker (default: "CLZ25.NYM")
        language (str): Language for output (default: "English")
        force_refresh (bool): Force regeneration even if cached data exists (default: False)
    
    Returns:
        dict: {
            'status': 'success' or 'error',
            'impact_metrics_df': DataFrame with impact metrics,
            'factor_time_df': DataFrame with factor date ranges,
            'meta_info': {
                'ticker': str,
                'calculated_beta': float,
                'language': str,
                'cached': bool,
                'cache_age_hours': float
            }
        }
    """
    
    try:
        print(f"\n{'='*80}")
        print(f"🚀 GETTING FACTOR METRICS FOR {ticker}")
        print(f"{'='*80}")
        
        # Initialize Redis client
        redis_client = RedisDatabaseStorage()
        storage_key = ticker.replace('.', '_').replace('=', '_')
        
        # Define Redis keys for the datasets
        impact_metrics_key = f"Crude_Oil:Future_Contract:{storage_key}:Impact_Metrics"
        factor_time_key = f"Crude_Oil:Future_Contract:{storage_key}:Factor_Time"
        metadata_key = f"Crude_Oil:Future_Contract:{storage_key}:Metadata"
        
        # Check if cached data exists and is fresh (< 7 days)
        if not force_refresh:
            print(f"\n📦 Checking cache...")
            
            # Define simple CSV keys
            impact_csv_key = f"Crude_Oil:Future_Contract:{storage_key}:Impact_Metrics.csv"
            factor_time_csv_key = f"Crude_Oil:Future_Contract:{storage_key}:Factor_Time.csv"
            
            # Try to retrieve CSV data from Redis
            impact_csv_data = redis_client.redis_client.get(impact_csv_key)
            factor_time_csv_data = redis_client.redis_client.get(factor_time_csv_key)
            
            # Check if both CSV files exist
            if impact_csv_data and factor_time_csv_data:
                print(f"✅ Using cached CSV data from Redis")
                
                # Convert CSV strings back to DataFrames
                impact_metrics_df = pd.read_csv(StringIO(impact_csv_data))
                factor_time_df = pd.read_csv(StringIO(factor_time_csv_data))
                
                # Try to retrieve metadata
                metadata = redis_client.get_json(metadata_key)
                if "error" not in metadata:
                    last_update = metadata.get('last_update', None)
                    calculated_beta = metadata.get('beta', None)
                    total_factors = metadata.get('total_factors', len(impact_metrics_df))
                    stored_language = metadata.get('language', language)  # Use stored language for consistency
                    
                    # Calculate cache age
                    if last_update:
                        try:
                            last_update_dt = datetime.fromisoformat(last_update)
                            cache_age = datetime.now() - last_update_dt
                            cache_age_hours = cache_age.total_seconds() / 3600
                            cache_age_days = cache_age.days
                            
                            # Check if data is stale (> 14 days)
                            if cache_age_days >= 14:
                                print(f"⚠️ Cache is stale ({cache_age_days} days old, >= 14 days)")
                                print(f"🔄 Performing incremental update...")
                                print(f"🌐 Using stored language: {stored_language}")
                                
                                # Perform incremental update with SAME language as stored data
                                updated_impact_df, updated_factor_time_df = await incremental_update_oil_metrics(
                                    ticker=ticker,
                                    previous_update_time=last_update,
                                    old_impact_metrics_df=impact_metrics_df,
                                    old_factor_time_df=factor_time_df,
                                    language=stored_language  # Use stored language for consistency
                                )
                                
                                # Store updated data
                                print(f"💾 Storing updated data...")
                                impact_csv_data = updated_impact_df.to_csv(index=False)
                                factor_time_csv_data = updated_factor_time_df.to_csv(index=False)
                                
                                redis_client.redis_client.set(impact_csv_key, impact_csv_data)
                                redis_client.redis_client.expire(impact_csv_key, 86400 * 7)
                                
                                redis_client.redis_client.set(factor_time_csv_key, factor_time_csv_data)
                                redis_client.redis_client.expire(factor_time_csv_key, 86400 * 7)
                                
                                # Update metadata
                                new_metadata = {
                                    "last_update": datetime.now().isoformat(),
                                    "ticker": ticker,
                                    "beta": calculated_beta,  # Keep old beta for now
                                    "total_factors": len(updated_impact_df),
                                    "language": language
                                }
                                redis_client.store_json(new_metadata, metadata_key)
                                
                                print(f"✅ Incremental update completed and stored!")
                                
                                return {
                                    'status': 'success',
                                    'impact_metrics_df': updated_impact_df,
                                    'factor_time_df': updated_factor_time_df,
                                    'meta_info': {
                                        'ticker': ticker,
                                        'calculated_beta': calculated_beta,
                                        'language': language,
                                        'cached': False,
                                        'last_update': new_metadata['last_update'],
                                        'total_factors': len(updated_impact_df),
                                        'cache_age_hours': 0,
                                        'cache_age_days': 0,
                                        'update_type': 'incremental'
                                    }
                                }
                            else:
                                print(f"✅ Cache is fresh ({cache_age_days} days old, < 14 days)")
                                
                        except Exception as e:
                            print(f"⚠️ Error during cache age check or incremental update: {e}")
                            cache_age_hours = None
                            cache_age_days = None
                    else:
                        cache_age_hours = None
                        cache_age_days = None
                else:
                    last_update = None
                    calculated_beta = None
                    total_factors = len(impact_metrics_df)
                    cache_age_hours = None
                    cache_age_days = None
                
                return {
                    'status': 'success',
                    'impact_metrics_df': impact_metrics_df,
                    'factor_time_df': factor_time_df,
                    'meta_info': {
                        'ticker': ticker,
                        'calculated_beta': calculated_beta,
                        'language': language,
                        'cached': True,
                        'last_update': last_update,
                        'total_factors': total_factors,
                        'cache_age_hours': cache_age_hours,
                        'cache_age_days': cache_age_days
                    }
                }
            
            print(f"📊 No cached CSV data found - generating fresh data...")
        else:
            print(f"🔄 Force refresh requested - generating fresh data...")
        
        # Step 1: Get/Update LLM Trend JSON from Redis
        print(f"\n📊 Step 1: Fetching LLM trend analysis...")
        print(f"🌐 Language: {language}")
        result = await get_llm_trend_summary(ticker, 700, language=language)
        print(f"✅ Retrieved trend analysis")
        
        # Step 2: Retrieve LLM trend from Redis
        print(f"\n📊 Step 2: Loading LLM trend from Redis...")
        llm_trend_json = redis_client.get_stored_data(
            "Crude_Oil", 
            "Future_Contract", 
            storage_key, 
            "LLM_Trend_Analyst_Result"
        )
        print(f"✅ Loaded LLM trend JSON")
        
        # Step 3: Generate Impact Metrics
        print(f"\n📊 Step 3: Generating impact metrics...")
        impact_result = get_oil_impact_from_existing_trends(
            llm_trend_json=llm_trend_json,
            ticker=ticker,
            risk_free_rate=0.025,
            language=language
        )
        
        if impact_result['status'] != 'success':
            return {
                'status': 'error',
                'error': impact_result.get('error', 'Unknown error in impact calculation')
            }
        
        print(f"✅ Impact metrics generated")
        
        # Extract the key outputs
        datasets = impact_result['datasets']
        impact_metrics_df = datasets['impact_metrics_df']
        factor_time_df = impact_result['factor_time_df']
        
        # Step 4: Store both datasets in Redis as CSV
        print(f"\n📦 Step 4: Storing datasets in Redis as CSV...")
        
        # Define simple CSV keys at the same level as LLM trend analysis
        impact_csv_key = f"Crude_Oil:Future_Contract:{storage_key}:Impact_Metrics.csv"
        factor_time_csv_key = f"Crude_Oil:Future_Contract:{storage_key}:Factor_Time.csv"
        
        # Convert DataFrames to CSV strings
        impact_csv_data = impact_metrics_df.to_csv(index=False)
        factor_time_csv_data = factor_time_df.to_csv(index=False)
        
        # Store directly in Redis with simple keys (7 days expiration)
        redis_client.redis_client.set(impact_csv_key, impact_csv_data)
        redis_client.redis_client.expire(impact_csv_key, 86400 * 7)
        
        redis_client.redis_client.set(factor_time_csv_key, factor_time_csv_data)
        redis_client.redis_client.expire(factor_time_csv_key, 86400 * 7)
        
        # Store metadata
        metadata = {
            "last_update": datetime.now().isoformat(),
            "ticker": ticker,
            "beta": impact_result['meta_info']['calculated_beta'],
            "total_factors": len(impact_metrics_df),
            "language": language
        }
        redis_client.store_json(metadata, metadata_key)
        
        print(f"✅ Stored Impact Metrics CSV: {impact_csv_key}")
        print(f"   Size: {len(impact_csv_data.encode('utf-8'))} bytes")
        print(f"✅ Stored Factor Time CSV: {factor_time_csv_key}")
        print(f"   Size: {len(factor_time_csv_data.encode('utf-8'))} bytes")
        print(f"✅ Stored Metadata: {metadata_key}")
        print(f"⏰ Cache expiration: 7 days")
        
        print(f"\n{'='*80}")
        print(f"✅ SUCCESS!")
        print(f"{'='*80}")
        print(f"📈 Beta: {impact_result['meta_info']['calculated_beta']:.4f}")
        print(f"📊 Impact Metrics: {len(impact_metrics_df)} factors")
        print(f"📅 Factor Time Ranges: {len(factor_time_df)} date ranges")
        print(f"💾 Data cached for 7 days")
        print(f"{'='*80}\n")
        
        return {
            'status': 'success',
            'impact_metrics_df': impact_metrics_df,
            'factor_time_df': factor_time_df,
            'meta_info': {
                'ticker': ticker,
                'calculated_beta': impact_result['meta_info']['calculated_beta'],
                'language': language,
                'cached': False,
                'last_update': datetime.now().isoformat(),
                'total_factors': len(impact_metrics_df),
                'cache_age_hours': 0
            }
        }
        
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return {
            'status': 'error',
            'error': str(e)
        }


def get_factor_metrics_sync(ticker: str = "CLZ25.NYM", language: str = "English", force_refresh: bool = False):
    """
    Synchronous wrapper for get_factor_metrics.
    Use this if you're not in an async context.
    
    Args:
        ticker (str): Oil futures ticker (default: "CLZ25.NYM")
        language (str): Language for output (default: "English")
        force_refresh (bool): Force regeneration even if cached data exists (default: False)
    """
    return asyncio.run(get_factor_metrics(ticker, language, force_refresh))



