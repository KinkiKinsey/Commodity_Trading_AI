#!/usr/bin/env python3
"""
Macro Analyst Agent
Analyzes macro-economic queries and provides comprehensive analysis.
"""

import sys
import os
from pathlib import Path

# Fix import paths for multiprocessing in Streamlit
current_dir = Path(__file__).parent.absolute()
if str(current_dir) not in sys.path:
    sys.path.insert(0, str(current_dir))

import json
import logging
import sys
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Union
import redis
from dataclasses import dataclass
from pathlib import Path
import asyncio
import re

# Import existing agents
from Macro_Read_Agent import MacroReadAgent

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('macro_analyst_agent.log')
    ]
)

class MacroAnalystAgent:
    """
    Macro Analyst Agent - Processes macro queries and stores results in user database
    """
    
    def __init__(self, user_id: str = None):
        """
        Initialize Macro Analyst Agent
        
        Args:
            user_id: User ID for database storage (if None, uses default)
        """
        self.user_id = user_id or "default_user"
        
        # Initialize Macro Read Agent
        self.macro_read_agent = MacroReadAgent()
        
        # Redis configuration for user database (same as other modular agents)
        self.redis_config = {
            "host": "redis-16204.fcrce180.us-east-1-1.ec2.redns.redis-cloud.com",
            "port": 16204,
            "username": "default",
            "password": "9rHiMKl63iYK9ja4qja6ZjnamuixS4UG"
        }
        
        # Redis client for user database
        self.redis_client = None
        self._connect_redis()
        
        # Database keys - Same structure as other agents
        self.macro_result_key = f"macro_result:{self.user_id}"
        self.macro_frontend_progress_key = f"macro_frontend_progress:{self.user_id}"
        
        print(f"🤖 Macro Analyst Agent initialized")
        print(f"👤 User ID: {self.user_id}")
        print(f"📊 Database: {self.redis_config['host']}:{self.redis_config['port']}")
        print(f"🔗 Integrated with: Macro Read Agent")
        print(f"📋 Output Format: FACT → EVIDENCE → RESULT structure")
        print(f"🗄️ Database Keys: {self.macro_result_key}, {self.macro_frontend_progress_key}")
        print(f"🔄 Logic: Always keep latest (overwrite previous)")
    
    def _connect_redis(self):
        """Connect to Redis user database"""
        try:
            self.redis_client = redis.Redis(
                host=self.redis_config["host"],
                port=self.redis_config["port"],
                username=self.redis_config["username"],
                password=self.redis_config["password"],
                decode_responses=True
            )
            self.redis_client.ping()
            print(f"✅ Redis connected: {self.redis_config['host']}:{self.redis_config['port']}")
        except Exception as e:
            print(f"❌ Redis connection failed: {e}")
            self.redis_client = None
    
    def process_macro_query(self, query: str) -> Dict[str, Any]:
        """
        Process macro query and return structured analysis
        
        Args:
            query: User's macro analysis question
            
        Returns:
            Dict containing analysis results and metadata
        """
        try:
            print(f"🔍 Processing macro query: {query}")
            
            # Update progress: Starting analysis
            self._update_progress("starting analysis", "started", 10, f"Initializing macro analysis for query: {query[:50]}...")
            
            # Get current timestamp
            timestamp = datetime.now().isoformat()
            
            # Update progress: Preprocessing query
            self._update_progress("preprocessing query", "started", 20, "Preparing query for Macro Read Agent")
            
            # Update progress: Calling Macro Read Agent
            self._update_progress("calling macro read agent", "started", 30, "Connecting to Macro Read Agent")
            print("📡 Calling Macro Read Agent...")
            analysis_response = self.macro_read_agent.process_user_query(query)
            
            if not analysis_response:
                self._update_progress("calling macro read agent", "failed", 30, "No response from Macro Read Agent")
                return {
                    'success': False,
                    'error': 'No response from Macro Read Agent',
                    'timestamp': timestamp,
                    'query': query
                }
            
            # Update progress: Processing response
            self._update_progress("processing response", "started", 60, "Processing LLM analysis response")
            
            # Update progress: Generating final result
            self._update_progress("generating final result", "started", 80, "Creating structured analysis result")
            
            # Create result structure
            result = {
                'success': True,
                'user_id': self.user_id,
                'query': query,
                'analysis': analysis_response,
                'timestamp': timestamp,
                'agent_type': 'Macro_Analyst_Agent',
                'data_source': 'Macro_Read_Agent',
                'output_format': 'FACT → EVIDENCE → RESULT',
                'metadata': {
                    'query_length': len(query),
                    'response_length': len(analysis_response),
                    'processing_time': datetime.now().isoformat()
                }
            }
            
            print(f"✅ Query processed successfully")
            print(f"📊 Response length: {len(analysis_response)} characters")
            
            # STORE THE RESULT IN USER ID DATABASE
            storage_success = self.store_macro_analysis(result)
            if storage_success:
                print(f"✅ Result stored in user ID database: {self.macro_result_key}")
            else:
                print(f"❌ Failed to store result in user ID database")
            
            return result
            
        except Exception as e:
            error_msg = f"Error processing macro query: {str(e)}"
            logging.error(error_msg)
            self._update_progress("processing query", "failed", 0, f"Error: {error_msg}")
            return {
                'success': False,
                'error': error_msg,
                'timestamp': datetime.now().isoformat(),
                'query': query
            }
    
    def _update_progress(self, step: str, status: str, progress: int = None, details: str = ""):
        """
        Update progress in Redis - same structure as other agents
        
        Args:
            step: Current step (e.g., "calling macro read agent", "generating analysis")
            status: Status (e.g., "started", "completed", "failed")
            progress: Progress percentage (0-100)
            details: Additional details
        """
        if not self.redis_client:
            print("⚠️ Redis not available for progress tracking")
            return
        
        try:
            progress_data = {
                "user_id": self.user_id,
                "step": step,
                "status": status,
                "progress": progress,
                "details": details,
                "timestamp": datetime.now().isoformat(),
                "agent": "macro_analyst"  # Identify this agent's data
            }
            
            # Store progress update in Redis - same structure as other agents
            progress_key = self.macro_frontend_progress_key
            
            # Get existing progress data
            existing_data = self.redis_client.hgetall(progress_key)
            
            # Create updated data structure
            updated_data = {}
            
            # Keep existing data from other agents
            for key, value in existing_data.items():
                try:
                    data = json.loads(value)
                    # Only keep data from other agents
                    if data.get("agent") != "macro_analyst":
                        updated_data[key] = value
                except:
                    # Keep non-JSON data (legacy)
                    updated_data[key] = value
            
            # Add/update Macro Analyst Agent data
            macro_key = f"macro_analyst:{step}"
            updated_data[macro_key] = json.dumps(progress_data)
            
            # Store all data back to Redis
            if updated_data:
                self.redis_client.hset(progress_key, mapping=updated_data)
            
            # Set expiry to clean up old progress (24 hours)
            self.redis_client.expire(progress_key, 86400)
            
            print(f"📊 Progress Update: {step} - {status} ({progress}%)")
            
        except Exception as e:
            print(f"❌ Failed to update progress: {e}")
            logging.error(f"Progress update error: {e}")

    def store_macro_analysis(self, analysis_result: Dict[str, Any]) -> bool:
        """
        Store macro analysis result in user database - Same structure as other agents
        
        Args:
            analysis_result: Analysis result from process_macro_query
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            if not self.redis_client:
                print("❌ Redis not connected. Cannot store analysis.")
                return False
            
            if not analysis_result.get('success'):
                print("⚠️ Analysis result indicates failure. Not storing.")
                return False
            
            # Update progress: Starting storage
            self._update_progress("storing analysis", "started", 90, "Storing macro analysis results")
            
            # Store macro result - OVERWRITES previous (latest only)
            result_key = self.macro_result_key
            result_data = json.dumps(analysis_result, default=str)
            
            result1 = self.redis_client.set(result_key, result_data)
            self.redis_client.expire(result_key, 30 * 24 * 60 * 60)  # 30 days
            
            # Update progress: Analysis complete
            self._update_progress("analysis complete", "completed", 100, "Macro analysis completed successfully")
            
            print(f"✅ Macro analysis stored successfully")
            print(f"📊 Result stored: {result_key}")
            print(f"📋 Progress stored: {self.macro_frontend_progress_key}")
            print(f"🔄 Previous data OVERWRITTEN (latest only kept)")
            
            return True
            
        except Exception as e:
            print(f"❌ Failed to store macro analysis: {e}")
            logging.error(f"Store macro analysis error: {e}")
            return False
    
    def _get_total_analyses_count(self) -> int:
        """Get total count of stored analyses"""
        try:
            if not self.redis_client:
                return 0
            
            # Count result entries for this user
            result_keys = self.redis_client.keys(f"macro_result:{self.user_id}")
            return len(result_keys)
            
        except Exception as e:
            logging.error(f"Error counting analyses: {e}")
            return 0
    
    def get_user_macro_analysis(self) -> Dict[str, Any]:
        """
        Get current macro analysis for user
        
        Returns:
            Dict containing current analysis or error
        """
        try:
            if not self.redis_client:
                return {'error': 'Redis not connected'}
            
            # Get current analysis
            result_data = self.redis_client.get(self.macro_result_key)
            if not result_data:
                return {'error': 'No current analysis found'}
            
            current_analysis = json.loads(result_data)
            
            # Get progress data
            progress_data = self.redis_client.get(self.macro_frontend_progress_key)
            progress = json.loads(progress_data) if progress_data else {}
            
            return {
                'current_analysis': current_analysis,
                'progress': progress,
                'retrieved_at': datetime.now().isoformat()
            }
            
        except Exception as e:
            return {'error': f'Error retrieving analysis: {str(e)}'}
    

    
    def run_macro_analysis(self, query: str) -> Dict[str, Any]:
        """
        Complete macro analysis workflow: process query and store result
        
        Args:
            query: User's macro analysis question
            
        Returns:
            Dict containing analysis result and storage status
        """
        try:
            print(f"🚀 Starting macro analysis workflow...")
            print(f"=" * 50)
            
            # Step 1: Process query
            print(f"📝 Step 1: Processing query...")
            analysis_result = self.process_macro_query(query)
            
            if not analysis_result.get('success'):
                print(f"❌ Query processing failed: {analysis_result.get('error')}")
                return analysis_result
            
            print(f"✅ Query processed successfully")
            
            # Step 2: Store result
            print(f"💾 Step 2: Storing analysis...")
            storage_success = self.store_macro_analysis(analysis_result)
            
            if storage_success:
                print(f"✅ Analysis stored successfully")
                analysis_result['stored'] = True
                analysis_result['storage_timestamp'] = datetime.now().isoformat()
            else:
                print(f"⚠️ Analysis storage failed")
                analysis_result['stored'] = False
            
            print(f"🎉 Macro analysis workflow completed!")
            print(f"=" * 50)
            
            return analysis_result
            
        except Exception as e:
            error_msg = f"Error in macro analysis workflow: {str(e)}"
            logging.error(error_msg)
            return {
                'success': False,
                'error': error_msg,
                'timestamp': datetime.now().isoformat(),
                'query': query
            }

def main():
    """
    Main execution function - Command Line Query Input
    """
    import sys
    import argparse
    
    # Set up argument parser
    parser = argparse.ArgumentParser(description='Macro Analyst Agent - Process macro queries')
    parser.add_argument('--queries', '-q', type=str, help='Macro analysis query')
    parser.add_argument('--user-id', '-u', type=str, default='default_user', help='User ID for database storage')
    
    # Parse arguments
    args = parser.parse_args()
    
    # Check if query provided
    if not args.queries:
        print("❌ No query provided!")
        print("Usage: python3 Macro_Analyst_Agent.py --queries 'Your macro question here'")
        print("Example: python3 Macro_Analyst_Agent.py --queries 'Why did PLTR go down recently?'")
        print("Or: python3 Macro_Analyst_Agent.py -q 'What economic indicators are available?'")
        sys.exit(1)
    
    try:
        # Initialize agent
        user_id = args.user_id
        agent = MacroAnalystAgent(user_id=user_id)
        
        # Run analysis workflow
        print(f"🔍 Processing query: {args.queries}")
        result = agent.run_macro_analysis(args.queries)
        
        if result.get('success'):
            print(f"\n📊 ANALYSIS RESULT:")
            print(f"Query: {result['query']}")
            print(f"Timestamp: {result['timestamp']}")
            print(f"Stored: {result.get('stored', False)}")
            print(f"\n{result['analysis']}")
        else:
            print(f"❌ Analysis failed: {result.get('error')}")
        
        print("="*50)
        print("✅ Analysis completed!")
                
    except Exception as e:
        print(f"❌ Main execution failed: {e}")
        logging.error(f"Main execution error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
