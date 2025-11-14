"""
Create Queries DataFrame
Merges Impact_Metrics, Factor_Time, and LLM_Trend_Summary into a single queries DataFrame
"""

import pandas as pd
from typing import Dict, Any, Optional
from datetime import datetime


def match_time_range_to_llm_trend(
    start_date: str,
    end_date: str,
    llm_trend_summary: Dict[str, Any]
) -> Optional[Dict[str, Any]]:
    """
    Match a time range (start_date, end_date) to an LLM trend entry.
    
    Args:
        start_date: Start date string (YYYY-MM-DD)
        end_date: End date string (YYYY-MM-DD)
        llm_trend_summary: LLM trend summary dict
        
    Returns:
        Matching trend dict with driver_type and AI_Reason, or None if no match
    """
    all_trends = {}
    
    # Combine current and historical trends
    if 'current_trends' in llm_trend_summary:
        all_trends.update(llm_trend_summary['current_trends'])
    if 'historical_trends' in llm_trend_summary:
        all_trends.update(llm_trend_summary['historical_trends'])
    
    # Try exact match first
    for trend_key, trend_data in all_trends.items():
        trend_time = trend_data.get('time', {})
        trend_start = trend_time.get('start', '')
        trend_end = trend_time.get('end', '')
        
        if trend_start == start_date and trend_end == end_date:
            summary = trend_data.get('summary', {})
            return {
                'driver_type': summary.get('driver_type', ''),
                'AI_Reason': trend_data.get('AI_Reason', '')
            }
    
    # If no exact match, try fuzzy match (within 1 day tolerance)
    start_dt = datetime.strptime(start_date, '%Y-%m-%d')
    end_dt = datetime.strptime(end_date, '%Y-%m-%d')
    
    for trend_key, trend_data in all_trends.items():
        trend_time = trend_data.get('time', {})
        trend_start_str = trend_time.get('start', '')
        trend_end_str = trend_time.get('end', '')
        
        if not trend_start_str or not trend_end_str:
            continue
            
        try:
            trend_start_dt = datetime.strptime(trend_start_str, '%Y-%m-%d')
            trend_end_dt = datetime.strptime(trend_end_str, '%Y-%m-%d')
            
            start_diff = abs((start_dt - trend_start_dt).days)
            end_diff = abs((end_dt - trend_end_dt).days)
            
            # Allow 1 day tolerance
            if start_diff <= 1 and end_diff <= 1:
                summary = trend_data.get('summary', {})
                return {
                    'driver_type': summary.get('driver_type', ''),
                    'AI_Reason': trend_data.get('AI_Reason', '')
                }
        except (ValueError, TypeError):
            continue
    
    return None


def create_queries_df(
    impact_metrics_df: pd.DataFrame,
    factor_time_df: pd.DataFrame,
    llm_trend_summary: Dict[str, Any]
) -> pd.DataFrame:
    """
    Create merged queries DataFrame combining Impact_Metrics, Factor_Time, and LLM_Trend_Summary.
    
    Structure:
    - Main key: factor name (from Impact_Metrics)
    - Sub-key: factor time ranges (from Factor_Time, left join)
    - Sub-sub-key: driver_type and AI_Reason (from LLM_Trend_Summary matched by time range)
    
    Args:
        impact_metrics_df: Impact metrics DataFrame with columns:
            - factor (factor name)
            - scope, trend_count, weighted_mean, weighted_variance, risk_reward_ratio, etc.
        factor_time_df: Factor time ranges DataFrame with columns:
            - factor_name (matches 'factor' in Impact_Metrics)
            - scope, start_date, end_date, time_interval, duration_days
        llm_trend_summary: LLM trend summary dict from get_llm_trend_summary()
            Must have 'llm_summary' -> 'current_trends' and 'historical_trends'
            Each trend has: time.start, time.end, summary.driver_type, AI_Reason
    
    Returns:
        Flattened DataFrame with columns:
        - All Impact_Metrics columns (factor, scope, weighted_mean, etc.)
        - All Factor_Time columns (start_date, end_date, duration_days, etc.)
        - driver_type, AI_Reason (matched from LLM trends)
        One row per factor-time range combination
    """
    # Extract llm_summary from structure if nested
    if 'llm_summary' in llm_trend_summary:
        llm_data = llm_trend_summary['llm_summary']
    else:
        llm_data = llm_trend_summary
    
    # Left join Impact_Metrics with Factor_Time on factor name
    # Impact_Metrics uses 'factor', Factor_Time uses 'factor_name'
    # Both have 'scope' column - drop from factor_time_df to avoid duplication (keep metrics scope)
    factor_time_for_merge = factor_time_df.copy()
    if 'scope' in factor_time_for_merge.columns:
        factor_time_for_merge = factor_time_for_merge.drop(columns=['scope'])
    
    merged_df = impact_metrics_df.merge(
        factor_time_for_merge,
        left_on='factor',
        right_on='factor_name',
        how='left'
    )
    
    # Initialize driver_type and AI_Reason columns
    merged_df['driver_type'] = ''
    merged_df['AI_Reason'] = ''
    
    # Match each time range to LLM trend and extract driver_type and AI_Reason
    for idx, row in merged_df.iterrows():
        start_date = row.get('start_date', '')
        end_date = row.get('end_date', '')
        
        if pd.isna(start_date) or pd.isna(end_date) or not start_date or not end_date:
            continue
        
        # Convert to string if needed
        start_date = str(start_date)[:10]  # Take first 10 chars to get YYYY-MM-DD
        end_date = str(end_date)[:10]
        
        # Match to LLM trend
        match_result = match_time_range_to_llm_trend(start_date, end_date, llm_data)
        
        if match_result:
            merged_df.at[idx, 'driver_type'] = match_result.get('driver_type', '')
            merged_df.at[idx, 'AI_Reason'] = match_result.get('AI_Reason', '')
    
    # Clean up: remove duplicate factor_name column (we already have 'factor')
    if 'factor_name' in merged_df.columns and 'factor' in merged_df.columns:
        merged_df = merged_df.drop(columns=['factor_name'])
    
    # Sort by factor, then by start_date
    merged_df = merged_df.sort_values(['factor', 'start_date']).reset_index(drop=True)
    
    # Calculate total_impact column: (1 + weighted_mean)^(average_duration) - 1
    if 'weighted_mean' in merged_df.columns and 'average_duration' in merged_df.columns:
        merged_df['total_impact'] = (1 + merged_df['weighted_mean']) ** merged_df['average_duration'] - 1
    else:
        # If columns don't exist, set to NaN
        merged_df['total_impact'] = None
    
    return merged_df

