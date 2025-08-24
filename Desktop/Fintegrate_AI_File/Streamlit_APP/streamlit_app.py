import streamlit as st
import redis
import json
import time
import asyncio
import threading
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
import multiprocessing
from multiprocessing import Pool, Manager
import os
import sys
from pathlib import Path
from datetime import datetime
import re

# Add current directory to Python path for imports
current_dir = Path(__file__).parent
sys.path.append(str(current_dir))

# Import the pipeline modules
from News_Verification import verify_statement_with_user
from Manager_Agent import quick_analysis
from Market_Expectation_Agent import MarketExpectationAgent
from Macro_Analyst_Agent import MacroAnalystAgent
from LLM_Call_Agent import LLMCallAgent

# Reload all modules to ensure latest versions
import importlib
import Manager_Agent
importlib.reload(Manager_Agent)

# Redis configuration
REDIS_CONFIG = {
    "host": "redis-16204.fcrce180.us-east-1-1.ec2.redns.redis-cloud.com",
    "port": 16204,
    "username": "default",
    "password": "9rHiMKl63iYK9ja4qja6ZjnamuixS4UG",
    "decode_responses": True
}

def get_redis_client():
    """Get Redis client connection"""
    try:
        import redis
        return redis.Redis(**REDIS_CONFIG)
    except Exception as e:
        st.error(f"Redis connection error: {e}")
        return None

def get_progress_data(user_id: str, agent_type: str):
    """Get progress data from Redis"""
    try:
        redis_client = get_redis_client()
        if not redis_client:
            return None
        
        key = f"{agent_type}_progress:{user_id}"
        key_type = redis_client.type(key)
        
        if key_type == b'HASH':
            data = redis_client.hgetall(key)
            return data
        elif key_type == b'STRING':
            data = redis_client.get(key)
            try:
                return json.loads(data) if data else None
            except json.JSONDecodeError:
                return data
        else:
            return None
    except Exception as e:
        st.error(f"Error getting progress: {e}")
        return None

def get_agent_result(user_id: str, agent_type: str):
    """Get agent result from Redis"""
    try:
        redis_client = get_redis_client()
        if not redis_client:
            return None
        
        key = f"{agent_type}_result:{user_id}"
        key_type = redis_client.type(key)
        
        if key_type == b'HASH':
            data = redis_client.hgetall(key)
            return data
        elif key_type == b'STRING':
            data = redis_client.get(key)
            try:
                return json.loads(data) if data else None
            except json.JSONDecodeError:
                return data
        else:
            return None
    except Exception as e:
        st.error(f"Error getting result: {e}")
        return None

def clean_agent_output(raw_output):
    """Clean and format agent output for better display"""
    if not raw_output:
        return "No output available"
    
    if isinstance(raw_output, str):
        # Log the raw output for debugging
        add_terminal_log(f"🔍 Raw output length: {len(raw_output)} characters", "info")
        add_terminal_log(f"🔍 Raw output preview: {raw_output[:100]}...", "info")
        
        # Clean up the trend mapping data
        cleaned = raw_output
        
        # Remove excessive whitespace and newlines
        cleaned = re.sub(r'\s+', ' ', cleaned)
        
        # Handle the corrupted SIMILAR TREND MAPPING output
        if 'SIMILAR TREND MAPPING:' in cleaned:
            add_terminal_log("🔍 Processing SIMILAR TREND MAPPING data", "info")
            try:
                # Split into sections
                parts = cleaned.split('SIMILAR TREND MAPPING:')
                if len(parts) > 1:
                    header = parts[0].strip()
                    trends_section = parts[1].strip()
                    
                    add_terminal_log(f"🔍 Header: {header[:50]}...", "info")
                    add_terminal_log(f"🔍 Trends section length: {len(trends_section)}", "info")
                    
                    # Clean up the corrupted text
                    # Remove random characters and fix broken text
                    trends_section = re.sub(r'[^\w\s\-\[\].,:<>()%]', '', trends_section)
                    trends_section = re.sub(r'\s+', ' ', trends_section)
                    
                    add_terminal_log(f"🔍 Cleaned trends section: {trends_section[:100]}...", "info")
                    
                    # Extract trend information using regex patterns
                    formatted_trends = []
                    
                    # Look for uptrend patterns
                    uptrend_matches = re.findall(r'uptrend\d+\s*\[([^]]+)\]', trends_section)
                    add_terminal_log(f"🔍 Found {len(uptrend_matches)} uptrend patterns", "info")
                    for i, match in enumerate(uptrend_matches):
                        if match:
                            dates = match.split(',')
                            if len(dates) >= 2:
                                start_date = dates[0].strip()
                                end_date = dates[1].strip()
                                formatted_trends.append(f"**📈 UPTREND {i+1}**: {start_date} to {end_date}")
                    
                    # Look for downtrend patterns
                    downtrend_matches = re.findall(r'downtrend\d+\s*\[([^]]+)\]', trends_section)
                    add_terminal_log(f"🔍 Found {len(downtrend_matches)} downtrend patterns", "info")
                    for i, match in enumerate(downtrend_matches):
                        if match:
                            dates = match.split(',')
                            if len(dates) >= 2:
                                start_date = dates[0].strip()
                                end_date = dates[1].strip()
                                formatted_trends.append(f"**📉 DOWNTREND {i+1}**: {start_date} to {end_date}")
                    
                    # Extract return data
                    return_matches = re.findall(r'day_avg_return:\s*([^,]+)', trends_section)
                    add_terminal_log(f"🔍 Found {len(return_matches)} return patterns", "info")
                    for match in return_matches:
                        if match.strip():
                            formatted_trends.append(f"**Average Daily Return**: {match.strip()}")
                    
                    # Extract duration
                    duration_matches = re.findall(r'duration:\s*([^,]+)', trends_section)
                    add_terminal_log(f"🔍 Found {len(duration_matches)} duration patterns", "info")
                    for match in duration_matches:
                        if match.strip():
                            formatted_trends.append(f"**Duration**: {match.strip()} days")
                    
                    # Extract volatility
                    volatility_matches = re.findall(r'volatility:\s*([^%]+%)', trends_section)
                    add_terminal_log(f"🔍 Found {len(volatility_matches)} volatility patterns", "info")
                    for match in volatility_matches:
                        if match.strip():
                            formatted_trends.append(f"**Volatility**: {match.strip()}")
                    
                    # If we couldn't parse anything, show the cleaned raw text
                    if not formatted_trends:
                        add_terminal_log("⚠️ No trends could be parsed, showing fallback", "warning")
                        # Try to extract any readable parts
                        readable_parts = []
                        if 'uptrend' in trends_section:
                            readable_parts.append("📈 Uptrend patterns detected")
                        if 'downtrend' in trends_section:
                            readable_parts.append("📉 Downtrend patterns detected")
                        if 'return' in trends_section:
                            readable_parts.append("📊 Return data available")
                        
                        if readable_parts:
                            formatted_trends = readable_parts
                        else:
                            # Show cleaned raw text as fallback
                            formatted_trends = [f"**Raw Output (Cleaned)**: {trends_section[:200]}..."]
                    
                    add_terminal_log(f"✅ Successfully formatted {len(formatted_trends)} trend items", "success")
                    
                    # Combine formatted output
                    if formatted_trends:
                        return f"""
**{header}**

**📊 Trend Analysis:**
{chr(10).join(formatted_trends)}
"""
                
            except Exception as e:
                # If parsing fails, return cleaned raw text
                add_terminal_log(f"❌ Error parsing trends: {str(e)}", "error")
                return f"""
**📊 Market Expectation Analysis (Raw Output):**

**Note**: Output parsing encountered issues. Showing cleaned text:

{cleaned[:500]}...

**Error**: {str(e)}
"""
        
        return cleaned
    
    elif isinstance(raw_output, dict):
        # Handle dictionary output
        if "error" in raw_output:
            return f"❌ Error: {raw_output['error']}"
        elif "status" in raw_output:
            return f"Status: {raw_output['status']}"
        else:
            return str(raw_output)
    
    return str(raw_output)

def add_terminal_log(message: str, log_type: str = "info"):
    """Add log to terminal and update display, also store in Redis for real-time sharing"""
    if 'terminal_logs' not in st.session_state:
        st.session_state.terminal_logs = []
    
    timestamp = datetime.now().strftime("%H:%M:%S")
    log_entry = {
        'timestamp': timestamp,
        'message': message,
        'type': log_type
    }
    
    # Add to session state
    st.session_state.terminal_logs.append(log_entry)
    
    # Keep only last 30 logs
    if len(st.session_state.terminal_logs) > 30:
        st.session_state.terminal_logs = st.session_state.terminal_logs[-30:]
    
    # Also store in Redis for real-time sharing across processes
    try:
        redis_client = redis.Redis(
            host="redis-16204.fcrce180.us-east-1-1.ec2.redns.redis-cloud.com",
            port=16204,
            username="default",
            password="9rHiMKl63iYK9ja4qja6ZjnamuixS4UG",
            decode_responses=True
        )
        
        # Store log in Redis with timestamp as key for ordering
        log_key = f"terminal_log:{int(time.time())}_{hash(message)}"
        redis_client.setex(log_key, 300, json.dumps(log_entry))  # 5 minute expiry
        
        # Store in a list for easy retrieval
        redis_client.lpush("terminal_logs_list", json.dumps(log_entry))
        redis_client.ltrim("terminal_logs_list", 0, 99)  # Keep last 100 logs
        
    except Exception as e:
        # If Redis fails, just continue with local logs
        pass

def display_terminal():
    """Display the AI terminal with current logs and auto-refresh capability"""
    if 'terminal_logs' not in st.session_state:
        st.session_state.terminal_logs = []
    
    # Create terminal container
    terminal_container = st.container()
    
    with terminal_container:
        # Add auto-refresh controls
        col1, col2, col3, col4 = st.columns([1, 1, 1, 1])
        
        with col1:
            if st.button("🔄 Enable Auto-Refresh", key="enable_refresh"):
                st.session_state.auto_refresh = True
                st.rerun()
        
        with col2:
            if st.button("⏹️ Stop Auto-Refresh", key="stop_refresh"):
                st.session_state.auto_refresh = False
                st.rerun()
        
        with col3:
            if st.button("📡 Manual Refresh", key="manual_refresh"):
                # Force immediate refresh
                st.rerun()
        
        with col4:
            if st.button("🧹 Clear Logs", key="clear_logs"):
                st.session_state.terminal_logs = []
                st.rerun()
        
        # Status display
        if 'auto_refresh' in st.session_state and st.session_state.auto_refresh:
            st.success("🔄 Auto-refresh ACTIVE - Updating every 2 seconds")
        else:
            st.info("⏸️ Auto-refresh INACTIVE - Click 'Enable' to start")
        
        # Show log count
        st.caption(f"📊 Total Logs: {len(st.session_state.terminal_logs)} | Last Update: {datetime.now().strftime('%H:%M:%S')}")
        
        # Terminal display
        st.markdown("""
        <div style="background: #0a0a0a; color: #00ff41; padding: 15px; border-radius: 10px; 
                    border: 2px solid #00ff41; font-family: 'Courier New', monospace; 
                    max-height: 300px; overflow-y: auto; box-shadow: 0 0 20px rgba(0, 255, 65, 0.3);">
            <div style="color: #00ff41; font-weight: bold; margin-bottom: 10px; font-size: 14px;">
                🤖 AI THINKING BOX
            </div>
        """, unsafe_allow_html=True)
        
        # Display logs with color coding
        for log in st.session_state.terminal_logs:
            color_map = {
                'info': '#00ff41',      # Green
                'success': '#00ff00',   # Bright Green
                'warning': '#ffff00',   # Yellow
                'error': '#ff0000'      # Red
            }
            color = color_map.get(log['type'], '#00ff41')
            
            st.markdown(f"""
            <div style="color: {color}; margin: 2px 0; font-size: 11px;">
                [{log['timestamp']}] {log['message']}
            </div>
            """, unsafe_allow_html=True)
        
        # Add blinking cursor
        st.markdown("""
            <span style="background: #00ff41; width: 8px; height: 12px; display: inline-block; 
                        animation: blink 1s infinite;"></span>
        </div>
        
        <style>
        @keyframes blink {
            0%, 50% { opacity: 1; }
            51%, 100% { opacity: 0; }
        }
        </style>
        """, unsafe_allow_html=True)
        
        # Auto-refresh logic
        if 'auto_refresh' in st.session_state and st.session_state.auto_refresh:
            # Check Redis for new logs every 2 seconds
            if 'last_refresh_time' not in st.session_state:
                st.session_state.last_refresh_time = time.time()
            
            current_time = time.time()
            if current_time - st.session_state.last_refresh_time >= 2:  # Every 2 seconds
                # Update refresh time
                st.session_state.last_refresh_time = current_time
                
                # Check Redis for new terminal logs
                try:
                    # Get latest logs from Redis
                    redis_client = redis.Redis(
                        host="redis-16204.fcrce180.us-east-1-1.ec2.redns.redis-cloud.com",
                        port=16204,
                        username="default",
                        password="9rHiMKl63iYK9ja4qja6ZjnamuixS4UG",
                        decode_responses=True
                    )
                    
                    # Get the latest logs from Redis list
                    redis_logs = redis_client.lrange("terminal_logs_list", 0, 99)  # Get last 100 logs
                    
                    # Check for new logs
                    new_logs_found = False
                    for redis_log in redis_logs:
                        try:
                            log_data = json.loads(redis_log)
                            if isinstance(log_data, dict) and 'message' in log_data:
                                # Check if this log is already in session state
                                existing_messages = [log['message'] for log in st.session_state.terminal_logs]
                                if log_data['message'] not in existing_messages:
                                    # Add new log to session state
                                    st.session_state.terminal_logs.append(log_data)
                                    new_logs_found = True
                        except:
                            pass
                    
                    # If new logs found, force refresh to show them
                    if new_logs_found:
                        # Keep only last 30 logs in session state
                        if len(st.session_state.terminal_logs) > 30:
                            st.session_state.terminal_logs = st.session_state.terminal_logs[-30:]
                        
                        # Force refresh to show new logs
                        st.rerun()
                    
                except Exception as e:
                    # If Redis fails, just continue with current logs
                    pass

def run_news_verification(user_question: str, user_id: str):
    """Run news verification pipeline with multiprocessing"""
    try:
        add_terminal_log(f"🔍 Starting Noise Filtering AI pipeline for User ID: {user_id}", "info")
        
        # Use multiprocessing to avoid Streamlit blocking
        with ProcessPoolExecutor(max_workers=1) as executor:
            add_terminal_log("⚡ Initializing multiprocessing executor...", "info")
            future = executor.submit(run_verification_process, user_question, user_id)
            add_terminal_log("🚀 Submitting Noise Filtering AI task to process pool...", "info")
            result = future.result(timeout=300)  # 5 minute timeout
        
        if result:
            add_terminal_log("✅ Noise Filtering AI completed successfully!", "success")
        else:
            add_terminal_log("❌ Noise Filtering AI failed", "error")
        
        return result
    except Exception as e:
        add_terminal_log(f"❌ Noise Filtering AI error: {e}", "error")
        st.error(f"Noise Filtering AI error: {e}")
        return None

def run_verification_process(user_question: str, user_id: str):
    """Multiprocessing wrapper for verification"""
    try:
        # Create new event loop for this process
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        # Run verification with multiprocessing
        result = loop.run_until_complete(verify_statement_with_user(
            statement=user_question,
            user_id=user_id,
            use_video=True
        ))
        
        loop.close()
        return result
    except Exception as e:
        return {"error": str(e)}

def run_manager_analysis(user_question: str, ticker: str, user_id: str):
    """Run manager agent analysis pipeline with multiprocessing"""
    try:
        add_terminal_log(f"🎯 Starting Impaction AI analysis for Ticker: {ticker}, User ID: {user_id}", "info")
        
        # Use multiprocessing to avoid Streamlit blocking
        with ProcessPoolExecutor(max_workers=1) as executor:
            add_terminal_log("⚡ Initializing Impaction AI process pool...", "info")
            future = executor.submit(run_manager_process, user_question, ticker, user_id)
            add_terminal_log("🚀 Submitting Impaction AI task to process pool...", "info")
            result = future.result(timeout=300)  # 5 minute timeout
        
        if result:
            add_terminal_log("✅ Impaction AI analysis completed successfully!", "success")
        else:
            add_terminal_log("❌ Impaction AI analysis failed", "error")
        
        return result
    except Exception as e:
        add_terminal_log(f"❌ Impaction AI error: {e}", "error")
        st.error(f"Impaction AI error: {e}")
        return None

def run_manager_process(user_question: str, ticker: str, user_id: str):
    """Multiprocessing wrapper for manager analysis"""
    try:
        # Create new event loop for this process
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        # Log the ticker being passed to the actual function
        print(f"🔍 Manager Process: Ticker received: {ticker}")
        
        # Run manager analysis with multiprocessing
        result = loop.run_until_complete(quick_analysis(
            user_query=user_question,
            ticker=ticker,
            user_id=user_id
        ))
        
        loop.close()
        return result
    except Exception as e:
        return {"error": str(e)}

def display_verification_details(verification_data):
    """Display comprehensive verification details"""
    if not verification_data:
        return
    
    # Handle both VerificationResult object and dictionary
    if hasattr(verification_data, 'final_decision'):
        # It's a VerificationResult object
        decision = verification_data.final_decision or 'Pending'
        reasoning = verification_data.final_reasoning or 'Processing...'
        reference_links = verification_data.reference_links or []
        filters = verification_data.filters or []
    else:
        # It's a dictionary
        decision = verification_data.get('final_decision', 'Pending')
        reasoning = verification_data.get('final_reasoning', 'Processing...')
        reference_links = verification_data.get('reference_links', [])
        filters = verification_data.get('filters', [])
    
    # Decision and Reasoning
    st.markdown("**📊 Verification Results:**")
    if decision == "Not Noise for Investment":
        st.success(f"✅ Decision: {decision}")
        st.session_state.verification_passed = True
    else:
        st.warning(f"⚠️ Decision: {decision}")
        st.session_state.verification_passed = False
    
    st.info(f"**Reasoning:** {reasoning}")
    
    # Filter Results
    if filters:
        st.markdown("**🔍 Filter Results:**")
        for filter_result in filters:
            if hasattr(filter_result, 'status'):
                status = filter_result.status.value if hasattr(filter_result.status, 'value') else filter_result.status
                name = filter_result.name
                details = filter_result.details
            else:
                status = filter_result.get('status', 'Unknown')
                name = filter_result.get('name', 'Unknown')
                details = filter_result.get('details', '')
            
            status_emoji = "✅" if status == "passed" else "❌" if status == "failed" else "⏭️"
            st.markdown(f"{status_emoji} **{name}**: {status}")
            if details:
                st.caption(f"Details: {details[:200]}...")
    
    # Reference Links
    if reference_links:
        st.markdown("**🔗 Reference Links:**")
        for link_data in reference_links:
            if isinstance(link_data, dict):
                url = link_data.get('url', '')
                title = link_data.get('title', '')
                if url:
                    if title:
                        st.markdown(f'📎 **{title}**<br><a href="{url}" target="_blank">{url}</a>', unsafe_allow_html=True)
                    else:
                        st.markdown(f'📎 <a href="{url}" target="_blank">{url}</a>', unsafe_allow_html=True)
            elif isinstance(link_data, str):
                st.markdown(f'📎 <a href="{link_data}" target="_blank">{link_data}</a>', unsafe_allow_html=True)

def main():
    # Page configuration
    st.set_page_config(
        page_title="Fintegrate AI - Financial Analysis Pipeline",
        page_icon="🚀",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Configure multiprocessing for Streamlit
    import multiprocessing
    
    # Enable multiprocessing in Streamlit
    multiprocessing.set_start_method('spawn', force=True)
    
    # Custom CSS for clean, essential design
    st.markdown("""
    <style>
    .main-header {
        text-align: center;
        padding: 20px 0;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border-radius: 10px;
        margin-bottom: 30px;
    }
    
    .input-section {
        background: #f8f9fa;
        padding: 20px;
        border-radius: 10px;
        margin-bottom: 30px;
        border: 1px solid #e9ecef;
    }
    
    .input-section .stTextInput {
        margin-bottom: 15px;
    }
    
    .input-section .stTextArea {
        margin-top: 20px;
    }
    
    .module-box {
        background: white;
        padding: 20px;
        border-radius: 10px;
        margin: 20px 0;
        border: 1px solid #e9ecef;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    
    .filter-container {
        display: flex;
        justify-content: space-around;
        margin: 20px 0;
    }
    
    .filter-icon {
        font-size: 2em;
        text-align: center;
        margin-bottom: 10px;
    }
    
    .filter-name {
        text-align: center;
        font-weight: bold;
        margin-bottom: 10px;
    }
    
    .agent-badge {
        background: #007bff;
        color: white;
        padding: 8px 16px;
        border-radius: 20px;
        display: inline-block;
        margin: 5px;
    }
    
    .result-section {
        background: #f8f9fa;
        padding: 15px;
        border-radius: 8px;
        margin: 10px 0;
    }
    
    .impaction-ai-box {
        background: linear-gradient(135deg, #a8edea 0%, #fed6e3 100%);
    }
    
    .sub-agent-card {
        background: #f8f9fa;
        padding: 15px;
        border-radius: 8px;
        margin: 10px 0;
    }
    
    .sub-agent-header {
        display: flex;
        align-items: center;
        margin-bottom: 15px;
    }
    
    .sub-agent-icon {
        font-size: 1.5em;
        margin-right: 10px;
    }
    
    .sub-agent-name {
        font-weight: bold;
        flex: 1;
    }
    
    .sub-agent-status {
        padding: 4px 12px;
        border-radius: 15px;
        font-size: 0.8em;
        font-weight: bold;
    }
    
    .status-processing {
        background: #fff3cd;
        color: #856404;
    }
    
    .status-complete {
        background: #d4edda;
        color: #155724;
    }
    
    .called-agents-display {
        background: #e3f2fd;
        padding: 15px;
        border-radius: 8px;
        margin: 15px 0;
    }
    
    .decision-step {
        background: #f8f9fa;
        padding: 8px 12px;
        border-radius: 6px;
        margin: 5px 0;
        border-left: 4px solid #007bff;
    }
    
    /* AI Terminal Window Styles */
    .ai-terminal-window {
        position: fixed;
        top: 20px;
        right: 20px;
        width: 350px;
        height: 300px;
        background: #0a0a0a;
        border: 2px solid #00ff41;
        border-radius: 10px;
        box-shadow: 0 0 20px rgba(0, 255, 65, 0.3);
        z-index: 1000;
        font-family: 'Courier New', monospace;
        overflow: hidden;
        animation: terminal-glow 2s ease-in-out infinite alternate;
    }
    
    .terminal-header {
        background: #00ff41;
        color: #000;
        padding: 8px 12px;
        font-weight: bold;
        font-size: 12px;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }
    
    .terminal-close {
        cursor: pointer;
        font-size: 14px;
        color: #000;
    }
    
    .terminal-content {
        padding: 12px;
        height: calc(100% - 40px);
        overflow-y: auto;
        color: #00ff41;
        font-size: 11px;
        line-height: 1.4;
    }
    
    .terminal-line {
        margin: 2px 0;
        word-wrap: break-word;
    }
    
    .terminal-line.info { color: #00ff41; }
    .terminal-line.success { color: #00ff00; }
    .terminal-line.warning { color: #ffff00; }
    .terminal-line.error { color: #ff0000; }
    .terminal-line.debug { color: #888888; }
    
    .terminal-cursor {
        display: inline-block;
        width: 8px;
        height: 12px;
        background: #00ff41;
        animation: blink 1s infinite;
    }
    
    @keyframes blink {
        0%, 50% { opacity: 1; }
        51%, 100% { opacity: 0; }
    }
    
    @keyframes terminal-glow {
        0% { box-shadow: 0 0 20px rgba(0, 255, 65, 0.3); }
        100% { box-shadow: 0 0 30px rgba(0, 255, 65, 0.6); }
    }
    
    .terminal-minimize {
        cursor: pointer;
        margin-right: 8px;
    }
    
    .terminal-minimized {
        height: 40px;
        overflow: hidden;
    }
    
    .terminal-minimized .terminal-content {
        display: none;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Main header
    st.markdown('<div class="main-header"><h1>🚀 Fintegrate AI</h1></div>', unsafe_allow_html=True)
    
    # AI Terminal Window - Native Streamlit (Actually Works!)
    st.markdown("**🤖 AI THINKING BOX**")
    
    # Add initial logs if terminal is empty
    if 'terminal_logs' not in st.session_state or not st.session_state.terminal_logs:
        add_terminal_log("🚀 AI Pipeline Terminal Active", "info")
        add_terminal_log("📡 Monitoring agent execution...", "info")
        add_terminal_log("🔍 Ready for real-time logs", "info")
        add_terminal_log("✅ Redis connection configured", "success")
        add_terminal_log("🤖 Agents loaded successfully", "success")
        add_terminal_log("🔄 Auto-refresh system ready - Click 'Enable Auto-Refresh' to start", "info")
    
    display_terminal()
    
    # Input section - simple, essential design
    with st.container():
        st.markdown('<div class="input-section">', unsafe_allow_html=True)
        
        # Top row: User ID and Ticker (left top small boxes)
        col1, col2, col3 = st.columns([1, 1, 4])
        with col1:
            user_id = st.text_input("User ID", value="", label_visibility="visible", placeholder="Enter User ID")
        with col2:
            ticker = st.text_input("Ticker", value="", label_visibility="visible", placeholder="Enter Ticker")
        
        # Below: Main query input (conversation chat box style) - takes whole middle part
        user_question = st.text_area(
            "Query",
            value="",
            height=120,
            label_visibility="visible",
            placeholder="Enter your financial analysis question..."
        )
        
        # Start button
        if st.button("🚀 Start Analysis", type="primary", use_container_width=True):
            # Validate inputs
            if not user_id.strip():
                st.error("❌ Please enter a User ID")
                return
            if not ticker.strip():
                st.error("❌ Please enter a Ticker")
                return
            if not user_question.strip():
                st.error("❌ Please enter a Query")
                return
            
            # Store inputs in session state for pipeline access
            st.session_state.current_user_id = user_id.strip()
            st.session_state.current_ticker = ticker.strip()
            st.session_state.current_user_question = user_question.strip()
            
            # Reset pipeline state for new run
            st.session_state.run_pipeline = False
            st.session_state.verification_result = None
            st.session_state.verification_passed = None
            st.session_state.manager_result = None
            st.session_state.sub_agent_results = None
            st.session_state.start_time = None
            
            # Clear terminal logs for fresh start
            if 'terminal_logs' in st.session_state:
                st.session_state.terminal_logs = []
            
            # Log the inputs being passed to the pipeline
            add_terminal_log(f"🚀 Starting NEW pipeline with User ID: {st.session_state.current_user_id}, Ticker: {st.session_state.current_ticker}", "info")
            add_terminal_log(f"📝 Query: {st.session_state.current_user_question[:100]}...", "info")
            add_terminal_log("🔄 Pipeline state reset - starting fresh analysis", "info")
            
            # All inputs valid, start pipeline
            st.session_state.run_pipeline = True
            st.session_state.start_time = time.time()
            st.rerun()
        
        # Reset Pipeline button
        if st.button("🔄 Reset Pipeline", type="secondary", use_container_width=True):
            # Clear all pipeline state
            st.session_state.run_pipeline = False
            st.session_state.verification_result = None
            st.session_state.verification_passed = None
            st.session_state.manager_result = None
            st.session_state.sub_agent_results = None
            st.session_state.start_time = None
            
            # Clear current input values
            if 'current_user_id' in st.session_state:
                del st.session_state.current_user_id
            if 'current_ticker' in st.session_state:
                del st.session_state.current_ticker
            if 'current_user_question' in st.session_state:
                del st.session_state.current_user_question
            
            # Clear terminal logs
            if 'terminal_logs' in st.session_state:
                st.session_state.terminal_logs = []
            
            # Add reset confirmation to terminal
            add_terminal_log("🔄 Pipeline reset - ready for new analysis", "info")
            st.rerun()
        
        # Show pipeline status
        if 'run_pipeline' in st.session_state and st.session_state.run_pipeline:
            st.info("🔄 Pipeline is currently running... Please wait for completion.")
        else:
            st.success("✅ Pipeline ready - Enter parameters and click 'Start Analysis'")
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Pipeline execution area
    if 'run_pipeline' not in st.session_state:
        st.session_state.run_pipeline = False
    
    if st.session_state.run_pipeline:
        st.markdown("---")
        
        # Step 1: News Verification (following your Jupyter notebook exactly)
        with st.container():
            st.markdown('<div class="module-box">', unsafe_allow_html=True)
            st.subheader("🔍 Noise Filtering AI")
            
            if 'verification_result' not in st.session_state or st.session_state.verification_result is None:
                # Show loading animation
                with st.spinner("🔍 Running Noise Filtering AI..."):
                    verification_result = run_news_verification(st.session_state.current_user_question, st.session_state.current_user_id)
                    if verification_result:
                        st.session_state.verification_result = verification_result
                        st.rerun()
                
                # Show progress while running
                st.info("🔄 Noise Filtering AI in progress... Please wait.")
            else:
                # Show verification results
                if st.session_state.verification_result:
                    display_verification_details(st.session_state.verification_result)
                    
                    # Button to view comprehensive results
                    with st.expander("📋 Click to view comprehensive Noise Filtering AI results", expanded=False):
                        st.markdown("**🔍 Detailed Noise Filtering AI Analysis:**")
                        if hasattr(st.session_state.verification_result, 'filters'):
                            for filter_result in st.session_state.verification_result.filters:
                                st.markdown(f"**{filter_result.name}**: {filter_result.status.value}")
                                if filter_result.details:
                                    st.caption(filter_result.details)
            
            st.markdown('</div>', unsafe_allow_html=True)
        
        # Step 2: Manager Agent (only if verification passed)
        if 'verification_passed' in st.session_state and st.session_state.verification_passed:
            with st.container():
                st.markdown('<div class="module-box impaction-ai-box">', unsafe_allow_html=True)
                st.subheader("🎯 Impaction AI")
                
                if 'manager_result' not in st.session_state or st.session_state.manager_result is None:
                    # Show loading animation
                    with st.spinner("🎯 Running Impaction AI..."):
                        manager_result = run_manager_analysis(st.session_state.current_user_question, st.session_state.current_ticker, st.session_state.current_user_id)
                        if manager_result:
                            st.session_state.manager_result = manager_result
                            st.rerun()
                    
                    # Show progress while running
                    st.info("🔄 Impaction AI in progress... Please wait.")
                else:
                    # Show manager results
                    st.success("✅ Impaction AI completed successfully!")
                    add_terminal_log("✅ Impecation Analyst AI completed successfully!", "success")
                    
                    # Check if sub-agents are completed
                    if st.session_state.manager_result and 'agent_results' in st.session_state.manager_result:
                        sub_agent_count = len(st.session_state.manager_result['agent_results'])
                        add_terminal_log(f"🎯 Impaction AI completed {sub_agent_count} sub-agents", "success")
                        
                        # Log each sub-agent completion
                        for agent_name, agent_result in st.session_state.manager_result['agent_results'].items():
                            if isinstance(agent_result, str) and agent_result.startswith("Error"):
                                add_terminal_log(f"❌ {agent_name} failed", "error")
                            else:
                                add_terminal_log(f"✅ {agent_name} completed successfully", "success")
                    
                    # Show which sub-agents will be called
                    st.markdown("**🎯 Sub-Agents Selected for Execution:**")
                    sub_agents_to_call = [
                        "Market Expectation Agent",
                        "Macro Analyst Agent"
                    ]
                    
                    for agent in sub_agents_to_call:
                        st.markdown(f'<div class="agent-badge">🤖 {agent}</div>', unsafe_allow_html=True)
                    
                    # Button to view comprehensive manager results
                    with st.expander("📋 Click to view comprehensive Impaction AI results", expanded=False):
                        st.markdown("**🧠 Impaction AI Analysis:**")
                        if isinstance(st.session_state.manager_result, dict):
                            if 'routing_analysis' in st.session_state.manager_result:
                                routing = st.session_state.manager_result['routing_analysis']
                                st.markdown(f"**Market Expectation:** {'✅ CALL' if routing.decision_call_market_expectation else '❌ SKIP'}")
                                st.markdown(f"**Revenue Segmentation:** {'✅ CALL' if routing.decision_call_revenue_segmentation else '❌ SKIP'}")
                                st.markdown(f"**Macro Analyst:** {'✅ CALL' if routing.decision_call_macro_analyst else '❌ SKIP'}")
                            
                            if 'agent_results' in st.session_state.manager_result:
                                st.markdown("**📊 Agent Results Summary:**")
                                for agent_name, result in st.session_state.manager_result['agent_results'].items():
                                    st.markdown(f"**{agent_name}:** {'✅ Success' if not str(result).startswith('Error') else '❌ Failed'}")
                            
                            if 'execution_summary' in st.session_state.manager_result:
                                summary = st.session_state.manager_result['execution_summary']
                                st.markdown("**📊 Execution Summary:**")
                                st.markdown(f"**Total Agents:** {summary.get('total_agents_executed', 0)}")
                                st.markdown(f"**Successful:** {summary.get('successful_executions', 0)}")
                                st.markdown(f"**Failed:** {summary.get('failed_executions', 0)}")
                
                st.markdown('</div>', unsafe_allow_html=True)
        
        # Step 3: Sub-Agents (only if manager completed)
        if 'manager_result' in st.session_state and st.session_state.manager_result is not None:
            with st.container():
                st.markdown('<div class="module-box">', unsafe_allow_html=True)
                st.subheader("🤖 Sub-Agents")
                
                # Check if we have sub-agent results from Manager Agent
                if 'agent_results' in st.session_state.manager_result:
                    st.success("🎉 Sub-Agents completed via Manager Agent!")
                    
                    # Get sub-agent results from Manager Agent (don't re-run!)
                    sub_agent_results = st.session_state.manager_result['agent_results']
                    
                    # Store in session state for display
                    st.session_state.sub_agent_results = sub_agent_results
                    
                    # Display results
                    for agent_name, agent_result in sub_agent_results.items():
                        # Log the agent result processing
                        add_terminal_log(f"🔍 Processing {agent_name} result", "info")
                        add_terminal_log(f"🔍 Result type: {type(agent_result).__name__}", "info")
                        if isinstance(agent_result, str):
                            add_terminal_log(f"🔍 Result length: {len(agent_result)} characters", "info")
                            add_terminal_log(f"🔍 Result preview: {agent_result[:100]}...", "info")
                        
                        with st.expander(f"📊 {agent_name} Results", expanded=True):
                            if isinstance(agent_result, str) and agent_result.startswith("Error"):
                                st.error(f"Error: {agent_result}")
                            else:
                                # Display natural output from sub-agents with consistent styling
                                if "Market_Expectation" in agent_name:
                                    # Market Expectation Agent - Clean, structured display
                                    st.markdown("""
                                    <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                                                color: white; padding: 15px; border-radius: 10px; margin-bottom: 20px;">
                                        <h3 style="margin: 0; color: white;">📈 Market Expectation Analysis</h3>
                                    </div>
                                    """, unsafe_allow_html=True)
                                    
                                    # Add summary section
                                    st.markdown("""
                                    <div style="background: #f8f9fa; padding: 10px; border-radius: 8px; 
                                                margin-bottom: 15px; border-left: 4px solid #667eea;">
                                        <strong>📋 Summary:</strong> Market expectation analysis completed successfully. 
                                        Analysis includes trend mapping and market insights for the specified ticker.
                                    </div>
                                    """, unsafe_allow_html=True)
                                    
                                    # Display raw output directly (no parsing)
                                    if isinstance(agent_result, str):
                                        st.markdown("**📊 Raw Analysis Output:**")
                                        # Show in a code block for better readability
                                        st.code(agent_result, language="text")
                                    else:
                                        st.markdown(f"""
**📊 Analysis Results:**

{agent_result}
""")
                                
                                elif "Macro_Analyst" in agent_name:
                                    # Macro Analyst Agent - Clean, structured display
                                    st.markdown("""
                                    <div style="background: linear-gradient(135deg, #a8edea 0%, #fed6e3 100%); 
                                                color: #333; padding: 10px; border-radius: 10px; margin-bottom: 20px;">
                                        <h3 style="margin: 0; color: #333;">🌍 Macro Analysis</h3>
                                    </div>
                                    """, unsafe_allow_html=True)
                                    
                                    if isinstance(agent_result, str):
                                        # Clean and format the result
                                        cleaned_result = clean_agent_output(agent_result)
                                        
                                        # Add summary section for consistency
                                        st.markdown("""
                                        <div style="background: #f8f9fa; padding: 10px; border-radius: 8px; 
                                                    margin-bottom: 15px; border-left: 4px solid #a8edea;">
                                            <strong>📋 Summary:</strong> Macro analysis completed successfully. 
                                            Analysis includes economic indicators and market impact assessment.
                                        </div>
                                        """, unsafe_allow_html=True)
                                        
                                        st.markdown(cleaned_result)
                                    else:
                                        st.markdown(f"""
                                        <div style="background: #f8f9fa; padding: 10px; border-radius: 8px; 
                                                    margin-bottom: 15px; border-left: 4px solid #a8edea;">
                                            <strong>📋 Summary:</strong> Macro analysis completed successfully.
                                        </div>
                                        """, unsafe_allow_html=True)
                                        
                                        st.markdown(f"""
**📊 Analysis Results:**

{agent_result}
""")
                                
                                else:
                                    # Handle other agent types with consistent styling
                                    st.markdown(f"""
                                    <div style="background: #f8f9fa; color: #333; padding: 15px; 
                                                border-radius: 10px; margin-bottom: 20px; border: 1px solid #e9ecef;">
                                        <h3 style="margin: 0; color: #333;">📊 {agent_name}</h3>
                                    </div>
                                    """, unsafe_allow_html=True)
                                    
                                    if isinstance(agent_result, str):
                                        cleaned_result = clean_agent_output(agent_result)
                                        st.markdown(cleaned_result)
                                    else:
                                        st.markdown(f"""
**📊 Analysis Results:**

{agent_result}
""")
                    
                    # Pipeline completion message and auto-reset option
                    st.markdown("---")
                    st.success("🎉 Pipeline Complete! All analysis results are ready.")
                    
                    # Show execution time
                    if 'start_time' in st.session_state and st.session_state.start_time:
                        elapsed_time = time.time() - st.session_state.start_time
                        st.info(f"⏱️ Total execution time: {elapsed_time:.0f} seconds")
                    
                    # Auto-reset option
                    if st.button("🔄 Run New Analysis", type="primary", use_container_width=True):
                        # Reset pipeline for new run
                        st.session_state.run_pipeline = False
                        st.session_state.verification_result = None
                        st.session_state.verification_passed = None
                        st.session_state.manager_result = None
                        st.session_state.sub_agent_results = None
                        st.session_state.start_time = None
                        
                        # Clear current input values
                        if 'current_user_id' in st.session_state:
                            del st.session_state.current_user_id
                        if 'current_ticker' in st.session_state:
                            del st.session_state.current_ticker
                        if 'current_user_question' in st.session_state:
                            del st.session_state.current_user_question
                        
                        # Clear terminal logs
                        if 'terminal_logs' in st.session_state:
                            st.session_state.terminal_logs = []
                        
                        add_terminal_log("🔄 Pipeline reset - ready for new analysis", "info")
                        st.rerun()
                
                # If no agent_results, show loading (this shouldn't happen if Manager completed)
                elif 'sub_agent_results' not in st.session_state or st.session_state.sub_agent_results is None:
                    st.info("🤖 Waiting for Impaction AI to complete sub-agent execution...")
                    
                    # Check Redis for Manager Agent progress
                    manager_progress = get_progress_data(st.session_state.current_user_id, "manager")
                    if manager_progress:
                        st.markdown("**📊 Impaction AI Progress:**")
                        for key, value in manager_progress.items():
                            if isinstance(value, str):
                                try:
                                    progress_data = json.loads(value)
                                    if 'step' in progress_data and 'status' in progress_data:
                                        step = progress_data['step']
                                        status = progress_data['status']
                                        progress = progress_data.get('progress', 0)
                                        
                                        if status == "completed":
                                            st.success(f"✅ {step}: {progress}%")
                                        elif status == "in_progress":
                                            st.info(f"🔄 {step}: {progress}%")
                                        else:
                                            st.info(f"⏳ {step}: {progress}%")
                                except:
                                    st.info(f"Progress: {value}")
                
                st.markdown('</div>', unsafe_allow_html=True)
    
    else:
        # Initial state - show instructions
        st.info("👆 Configure your parameters above and click 'Start Analysis' to begin")

if __name__ == "__main__":
    main()
