"""
Oil Impact Incremental Update - Helper Functions
=================================================
This module provides helper functions for incremental update of oil impact metrics.
Directly adapted from Quant_Impact_Incremental_Update.py

Key Functions:
- extract_factor_names: Extract factor names from DataFrame
- map_factors_with_llm: Use LLM to map new factors to old factors
- merge_impact_metrics: Merge old and new impact metrics with mapping
- update_impact_metrics_with_new_factors: Update metrics with weighted average
- merge_factor_time_data: Merge old and new factor time data
"""

import pandas as pd
import json
import sys
from pathlib import Path
from typing import List, Dict, Any, Tuple

# Add workspace root to path
workspace_root = Path(__file__).parent.parent
if str(workspace_root) not in sys.path:
    sys.path.insert(0, str(workspace_root))

from .Oil_LLM_Source.LLM_Call_Agent import LLMCallAgent
from DataBase_Connection_Source.RedisDatabaseStorage import RedisDatabaseStorage


# =============================================================================
# STEP 2.1: EXTRACT FACTOR NAMES
# =============================================================================

def extract_factor_names(impact_df: pd.DataFrame) -> List[str]:
    """
    Extract factor names from impact metrics DataFrame.
    
    Args:
        impact_df: DataFrame with impact metrics
        
    Returns:
        List of factor names
    """
    if 'factor' in impact_df.columns:
        return impact_df['factor'].tolist()
    elif 'factor_name' in impact_df.columns:
        return impact_df['factor_name'].tolist()
    elif impact_df.index.name == 'factor_name':
        return impact_df.index.tolist()
    else:
        # Try to extract from index if it's a string index
        return [str(idx) for idx in impact_df.index]


# =============================================================================
# STEP 2.2: LLM FACTOR MAPPING
# =============================================================================

def map_factors_with_llm(
    new_factors: List[str], 
    old_factors: List[str], 
    ticker: str
) -> Dict[str, Any]:
    """
    Use LLM to map new factors to old factors or identify new ones.
    EXACT COPY from stock system - works for oil too!
    
    Args:
        new_factors: List of new factor names
        old_factors: List of old factor names
        ticker: Oil ticker (e.g., "CLZ25.NYM")
        
    Returns:
        Dictionary with mapping results:
        {
            "mappings": [
                {
                    "new_factor": "factor_name",
                    "type": "existing" or "new",
                    "existing_index": 0,  // only if type is "existing"
                    "existing_factor": "existing_factor_name"  // only if type is "existing"
                }
            ]
        }
    """
    llm_agent = LLMCallAgent()
    
    prompt = f"""
You are an oil market factor mapping expert. I need you to map new factors to existing factors for {ticker} crude oil analysis.

EXISTING FACTORS:
{json.dumps(old_factors, indent=2)}

NEW FACTORS:
{json.dumps(new_factors, indent=2)}

TASK:
1. For each new factor, determine if it's similar to any existing factor
2. If similar, provide the index of the existing factor (0-based)
3. If not similar, mark it as "new"

OUTPUT FORMAT (JSON):
{{
    "mappings": [
        {{
            "new_factor": "factor_name",
            "type": "existing" or "new",
            "existing_index": 0,  // only if type is "existing"
            "existing_factor": "existing_factor_name"  // only if type is "existing"
        }}
    ]
}}

RULES:
- Be conservative: only map if factors are clearly similar (same concept, different wording)
- Consider synonyms, abbreviations, and different phrasings
- If unsure, mark as "new"
- Focus on oil market and macroeconomic concepts
- "OPEC+ Production Cut" matches "OPEC+ Supply Reduction"
- "Inventory Decline Better Than Expected" matches "Storage Draw Better Than Expected"
"""
    
    try:
        response = llm_agent.call_deepseek(prompt)
        
        # Parse JSON response
        if isinstance(response, str):
            # Try to extract JSON from response
            start_idx = response.find('{')
            end_idx = response.rfind('}') + 1
            if start_idx != -1 and end_idx != 0:
                json_str = response[start_idx:end_idx]
                result = json.loads(json_str)
            else:
                raise ValueError("No valid JSON found in response")
        else:
            result = response
            
        return result
        
    except Exception as e:
        print(f"❌ LLM mapping failed: {e}")
        # Fallback: mark all as new
        return {
            "mappings": [
                {
                    "new_factor": factor,
                    "type": "new"
                }
                for factor in new_factors
            ]
        }


# =============================================================================
# STEP 2.3: MERGE IMPACT METRICS
# =============================================================================

def merge_impact_metrics(
    new_impact_df: pd.DataFrame,
    old_impact_metrics_df: pd.DataFrame,
    ticker: str
) -> pd.DataFrame:
    """
    Merge new and old impact metrics using LLM-based factor mapping.
    EXACT COPY from stock system - works for oil too!
    
    Args:
        new_impact_df: New impact metrics DataFrame
        old_impact_metrics_df: Old impact metrics DataFrame
        ticker: Oil ticker for context
        
    Returns:
        Merged impact metrics DataFrame with mapping_new_factors column
    """
    print(f"🔄 Merging impact metrics for {ticker}...")
    
    # Extract factor names
    new_factors = extract_factor_names(new_impact_df)
    old_factors = extract_factor_names(old_impact_metrics_df)
    
    print(f"📊 New factors: {len(new_factors)}")
    print(f"📊 Old factors: {len(old_factors)}")
    
    # Get LLM mapping
    print("🤖 Getting LLM factor mapping...")
    mapping_result = map_factors_with_llm(new_factors, old_factors, ticker)
    
    # Start with old impact metrics as base - keep only essential columns
    essential_columns = [
        'scope', 'factor', 'trend_count', 'weighted_mean', 'weighted_variance',
        'average_duration', 'total_duration', 'trend_weight_score',
        'score_weighted_mean', 'score_weighted_variance', 'risk_reward_ratio'
    ]
    
    # Filter to only keep essential columns that exist
    available_columns = [col for col in essential_columns if col in old_impact_metrics_df.columns]
    merged_df = old_impact_metrics_df[available_columns].copy()
    
    # Add mapping column
    merged_df['mapping_new_factors'] = ""
    
    # Process each new factor
    for mapping in mapping_result.get('mappings', []):
        new_factor = mapping['new_factor']
        mapping_type = mapping['type']
        
        if mapping_type == 'existing':
            # Map to existing factor
            existing_index = mapping['existing_index']
            existing_factor = mapping['existing_factor']
            
            print(f"✅ Mapping '{new_factor}' → '{existing_factor}' (index {existing_index})")
            
            # Add to mapping column
            if merged_df.iloc[existing_index]['mapping_new_factors']:
                merged_df.iloc[existing_index, merged_df.columns.get_loc('mapping_new_factors')] += f", {new_factor}"
            else:
                merged_df.iloc[existing_index, merged_df.columns.get_loc('mapping_new_factors')] = new_factor
                
        elif mapping_type == 'new':
            # Add as new row
            print(f"➕ Adding new factor: '{new_factor}'")
            
            # Get the new factor's data - handle both 'factor' and 'factor_name' columns
            if 'factor' in new_impact_df.columns:
                new_factor_data = new_impact_df[new_impact_df['factor'] == new_factor].iloc[0]
            elif 'factor_name' in new_impact_df.columns:
                new_factor_data = new_impact_df[new_impact_df['factor_name'] == new_factor].iloc[0]
            else:
                print(f"❌ Cannot find factor column in new_impact_df")
                continue
            
            # Create new row with only essential columns
            new_row = {}
            for col in available_columns:
                if col in new_factor_data:
                    new_row[col] = new_factor_data[col]
                else:
                    new_row[col] = None  # Fill missing columns with None
            
            new_row['mapping_new_factors'] = ""
            
            # Add to merged DataFrame
            merged_df = pd.concat([merged_df, pd.DataFrame([new_row])], ignore_index=True)
    
    print(f"✅ Merge completed: {len(merged_df)} total factors")
    print(f"📋 Columns kept: {list(merged_df.columns)}")
    return merged_df


# =============================================================================
# STEP 2.4: UPDATE IMPACT METRICS WITH NEW DATA
# =============================================================================

def update_impact_metrics_with_new_factors(
    merged_df: pd.DataFrame, 
    new_impact_df: pd.DataFrame
) -> pd.DataFrame:
    """
    Update impact metrics for factors that have new factor mappings.
    Recalculate weighted metrics based on old and new data.
    EXACT COPY from stock system - works for oil too!
    
    Args:
        merged_df: Merged DataFrame with mapping_new_factors column
        new_impact_df: New impact metrics DataFrame
        
    Returns:
        Updated impact metrics DataFrame
    """
    print("🔄 Updating impact metrics with new factor data...")
    
    updated_df = merged_df.copy()
    
    # Process each row that has new factor mappings
    for idx, row in updated_df.iterrows():
        if row['mapping_new_factors'] and row['mapping_new_factors'] != '':
            # Get the new factor names
            new_factors = [factor.strip() for factor in row['mapping_new_factors'].split(',')]
            
            print(f"📊 Updating factor: {row['factor']} with new factors: {new_factors}")
            
            # Get new factor data
            new_factor_data = []
            for new_factor in new_factors:
                if 'factor' in new_impact_df.columns:
                    new_data = new_impact_df[new_impact_df['factor'] == new_factor]
                elif 'factor_name' in new_impact_df.columns:
                    new_data = new_impact_df[new_impact_df['factor_name'] == new_factor]
                else:
                    continue
                
                if not new_data.empty:
                    new_factor_data.append(new_data.iloc[0])
            
            if not new_factor_data:
                continue
            
            # Calculate old metrics
            old_weighted_mean = row['weighted_mean']
            old_weighted_variance = row['weighted_variance']
            old_total_duration = row['total_duration']
            old_trend_count = row['trend_count']
            
            # Calculate new metrics
            new_total_duration = sum([data['total_duration'] for data in new_factor_data])
            new_trend_count = sum([data['trend_count'] for data in new_factor_data])
            new_weighted_mean = sum([data['weighted_mean'] * data['total_duration'] for data in new_factor_data]) / new_total_duration if new_total_duration > 0 else 0
            new_weighted_variance = sum([data['weighted_variance'] * data['total_duration'] for data in new_factor_data]) / new_total_duration if new_total_duration > 0 else 0
            
            # Calculate combined metrics using weighted average
            combined_total_duration = old_total_duration + new_total_duration
            old_weight = old_total_duration / combined_total_duration if combined_total_duration > 0 else 0
            new_weight = new_total_duration / combined_total_duration if combined_total_duration > 0 else 0
            
            # Update weighted mean and variance
            updated_weighted_mean = old_weight * old_weighted_mean + new_weight * new_weighted_mean
            updated_weighted_variance = old_weight * old_weighted_variance + new_weight * new_weighted_variance
            
            # Update other metrics
            updated_trend_count = old_trend_count + new_trend_count
            updated_average_duration = combined_total_duration / updated_trend_count if updated_trend_count > 0 else 0
            
            # Recalculate derived metrics
            import numpy as np
            total_trends = updated_df['trend_count'].sum() + new_trend_count - old_trend_count
            updated_trend_weight_score = updated_trend_count / total_trends if total_trends > 0 else 0
            updated_score_weighted_mean = updated_trend_weight_score * updated_weighted_mean
            updated_score_weighted_variance = updated_trend_weight_score * updated_weighted_variance
            updated_risk_reward_ratio = np.abs(updated_weighted_mean) / np.sqrt(updated_weighted_variance) if updated_weighted_variance > 0 else 0
            
            # Update the row
            updated_df.at[idx, 'trend_count'] = updated_trend_count
            updated_df.at[idx, 'weighted_mean'] = updated_weighted_mean
            updated_df.at[idx, 'weighted_variance'] = updated_weighted_variance
            updated_df.at[idx, 'average_duration'] = updated_average_duration
            updated_df.at[idx, 'total_duration'] = combined_total_duration
            updated_df.at[idx, 'trend_weight_score'] = updated_trend_weight_score
            updated_df.at[idx, 'score_weighted_mean'] = updated_score_weighted_mean
            updated_df.at[idx, 'score_weighted_variance'] = updated_score_weighted_variance
            updated_df.at[idx, 'risk_reward_ratio'] = updated_risk_reward_ratio
            
            print(f"✅ Updated {row['factor']}: mean={updated_weighted_mean:.6f}, variance={updated_weighted_variance:.6f}")
    
    print(f"✅ Impact metrics update completed for {len(updated_df)} factors")
    return updated_df


# =============================================================================
# STEP 2.5: CLEANUP TEMPORARY COLUMNS
# =============================================================================

def cleanup_impact_metrics_df(df: pd.DataFrame) -> pd.DataFrame:
    """
    Clean up the impact metrics DataFrame by removing temporary columns.
    
    Args:
        df: DataFrame with potential temporary columns
        
    Returns:
        Cleaned DataFrame
    """
    cleaned_df = df.copy()
    
    # Remove mapping_new_factors column if it exists
    if 'mapping_new_factors' in cleaned_df.columns:
        cleaned_df = cleaned_df.drop('mapping_new_factors', axis=1)
        print("🧹 Cleaned up: Removed 'mapping_new_factors' column")
    
    print(f"✅ DataFrame cleaned: {len(df.columns)} → {len(cleaned_df.columns)} columns")
    return cleaned_df


# =============================================================================
# STEP 2.6: MERGE FACTOR TIME DATA
# =============================================================================

def merge_factor_time_data(
    old_factor_time_df: pd.DataFrame,
    new_factor_time_df: pd.DataFrame,
    ticker: str,
    language: str = "English"
) -> pd.DataFrame:
    """
    Merge old and new factor time data using LLM to map similar factors.
    EXACT COPY from stock system - works for oil too!
    
    Args:
        old_factor_time_df: Existing factor time DataFrame
        new_factor_time_df: New factor time DataFrame
        ticker: Oil ticker symbol
        language: Language for output
        
    Returns:
        Merged factor time DataFrame with combined time intervals
    """
    print("🔄 Merging factor time data using LLM mapping...")
    
    # Extract unique factors from both DataFrames
    old_factors = old_factor_time_df['factor_name'].unique().tolist()
    new_factors = new_factor_time_df['factor_name'].unique().tolist()
    
    print(f"📊 Old factors: {len(old_factors)}")
    print(f"📊 New factors: {len(new_factors)}")
    
    # Get LLM mapping
    mapping_result = map_factors_with_llm(new_factors, old_factors, ticker)
    factor_mapping = {}
    
    for mapping in mapping_result.get('mappings', []):
        new_factor = mapping['new_factor']
        if mapping['type'] == 'existing':
            factor_mapping[new_factor] = mapping['existing_factor']
        else:
            factor_mapping[new_factor] = None
    
    print(f"✅ Factor mapping completed")
    print(f"   Mapped factors: {len([k for k, v in factor_mapping.items() if v is not None])}")
    print(f"   New factors: {len([k for k, v in factor_mapping.items() if v is None])}")
    
    # Create merged DataFrame
    merged_data = []
    
    # Add all old factor time data (keep as-is)
    for _, row in old_factor_time_df.iterrows():
        merged_data.append({
            'factor_name': row['factor_name'],
            'scope': row['scope'],
            'start_date': row['start_date'],
            'end_date': row['end_date'],
            'time_interval': row['time_interval'],
            'duration_days': row['duration_days']
        })
    
    # Process new factor time data
    for _, row in new_factor_time_df.iterrows():
        new_factor_name = row['factor_name']
        mapped_old_factor = factor_mapping.get(new_factor_name)
        
        if mapped_old_factor is not None:
            # This factor maps to an existing old factor - use old factor name
            merged_data.append({
                'factor_name': mapped_old_factor,  # Use old factor name
                'scope': row['scope'],
                'start_date': row['start_date'],
                'end_date': row['end_date'],
                'time_interval': row['time_interval'],
                'duration_days': row['duration_days']
            })
            print(f"   🔄 Mapped '{new_factor_name}' → '{mapped_old_factor}'")
        else:
            # This is a completely new factor - keep new factor name
            merged_data.append({
                'factor_name': new_factor_name,
                'scope': row['scope'],
                'start_date': row['start_date'],
                'end_date': row['end_date'],
                'time_interval': row['time_interval'],
                'duration_days': row['duration_days']
            })
            print(f"   ➕ Added new factor: '{new_factor_name}'")
    
    # Create merged DataFrame
    merged_factor_time_df = pd.DataFrame(merged_data)
    
    # Sort by factor_name and start_date
    merged_factor_time_df = merged_factor_time_df.sort_values(['factor_name', 'start_date']).reset_index(drop=True)
    
    print(f"\n✅ Factor time data merged successfully!")
    print(f"   Total time intervals: {len(merged_factor_time_df)}")
    print(f"   Unique factors: {len(merged_factor_time_df['factor_name'].unique())}")
    
    return merged_factor_time_df


# =============================================================================
# STEP 3: MAIN INCREMENTAL UPDATE FUNCTION
# =============================================================================

async def incremental_update_oil_metrics(
    ticker: str,
    previous_update_time: str,
    old_impact_metrics_df: pd.DataFrame,
    old_factor_time_df: pd.DataFrame,
    language: str = "English"
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Main function to perform incremental update of oil impact metrics.
    
    This function:
    1. Generates new metrics from previous_update_time to today
    2. Uses LLM to map new factors to old factors
    3. Merges impact metrics with weighted average
    4. Merges factor time data
    
    Args:
        ticker: Oil ticker (e.g., "CLZ25.NYM")
        previous_update_time: ISO timestamp of last update (e.g., "2025-10-07T21:38:14")
        old_impact_metrics_df: Existing impact metrics DataFrame
        old_factor_time_df: Existing factor time DataFrame
        language: Language for output (default: "English")
        
    Returns:
        Tuple of (updated_impact_metrics_df, updated_factor_time_df)
    """
    from datetime import datetime
    from Oil_Impact_Metrics import get_oil_impact_from_existing_trends
    from LLM_Trend_Summary import get_llm_trend_summary
    from DataBase_Connection_Source.RedisDatabaseStorage import RedisDatabaseStorage
    
    print(f"\n{'='*80}")
    print(f"🔄 INCREMENTAL UPDATE FOR {ticker}")
    print(f"{'='*80}")
    print(f"📅 Previous update: {previous_update_time}")
    print(f"📅 Current time: {datetime.now().isoformat()}")
    print(f"{'='*80}\n")
    
    try:
        # Step 1: Get NEW LLM trend data with incremental filtering
        print(f"📊 Step 1: Fetching NEW trend analysis (from {previous_update_time} to today)...")
        print(f"🌐 Language: {language}")
        result = await get_llm_trend_summary(
            ticker=ticker,
            days=700,
            force_refresh=True,  # Force refresh to get latest
            incremental_since=previous_update_time,  # Filter news from this date onwards
            language=language  # Pass language for consistent factor generation
        )
        
        # Check if no new data found
        if result is None:
            print(f"⚠️ No new news/trends found since {previous_update_time}")
            print(f"ℹ️ Returning existing data unchanged")
            return old_impact_metrics_df, old_factor_time_df
        
        print(f"✅ NEW trends created from filtered news")
        
        # Step 2: Retrieve NEW LLM trend from Redis
        print(f"📊 Step 2: Loading updated LLM trend from Redis...")
        redis_client = RedisDatabaseStorage()
        storage_key = ticker.replace('.', '_').replace('=', '_')
        llm_trend_json = redis_client.get_stored_data(
            "Crude_Oil", 
            "Future_Contract", 
            storage_key, 
            "LLM_Trend_Analyst_Result"
        )
        
        # Step 3: Generate NEW impact metrics from filtered trends only
        print(f"📊 Step 3: Generating impact metrics from incremental trends...")
        impact_result = get_oil_impact_from_existing_trends(
            llm_trend_json=llm_trend_json,
            ticker=ticker,
            risk_free_rate=0.025,
            language=language,
            incremental_since=previous_update_time  # Pass incremental date for filtering
        )
        
        if impact_result['status'] != 'success':
            raise Exception(f"Impact calculation failed: {impact_result.get('error', 'Unknown error')}")
        
        # Extract new metrics
        new_impact_metrics_df = impact_result['datasets']['impact_metrics_df']
        new_factor_time_df = impact_result['factor_time_df']
        
        print(f"✅ Generated metrics:")
        print(f"   New impact metrics: {len(new_impact_metrics_df)} factors")
        print(f"   New factor time: {len(new_factor_time_df)} intervals")
        
        # Step 4: LLM-based factor mapping and merge
        print(f"\n🤖 Step 4: LLM-based factor mapping...")
        merged_impact_df = merge_impact_metrics(
            new_impact_df=new_impact_metrics_df,
            old_impact_metrics_df=old_impact_metrics_df,
            ticker=ticker
        )
        
        # Step 5: Update metrics with weighted average
        print(f"\n📊 Step 5: Updating metrics with weighted average...")
        updated_impact_df = update_impact_metrics_with_new_factors(
            merged_df=merged_impact_df,
            new_impact_df=new_impact_metrics_df
        )
        
        # Step 6: Cleanup temporary columns
        print(f"\n🧹 Step 6: Cleaning up...")
        final_impact_df = cleanup_impact_metrics_df(updated_impact_df)
        
        # Step 7: Merge factor time data
        print(f"\n📅 Step 7: Merging factor time data...")
        final_factor_time_df = merge_factor_time_data(
            old_factor_time_df=old_factor_time_df,
            new_factor_time_df=new_factor_time_df,
            ticker=ticker,
            language=language
        )
        
        print(f"\n{'='*80}")
        print(f"✅ INCREMENTAL UPDATE COMPLETED!")
        print(f"{'='*80}")
        print(f"📊 Final metrics:")
        print(f"   Impact metrics: {len(final_impact_df)} factors")
        print(f"   Factor time: {len(final_factor_time_df)} intervals")
        print(f"{'='*80}\n")
        
        return final_impact_df, final_factor_time_df
        
    except Exception as e:
        print(f"\n❌ Incremental update failed: {e}")
        import traceback
        traceback.print_exc()
        raise e

